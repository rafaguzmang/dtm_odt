from odoo import api,models,fields
from datetime import datetime
from odoo.exceptions import ValidationError
from fractions import Fraction
import re
import pytz
import os

class DtmOdt(models.Model):
    _name = "dtm.odt"
    _inherit = ['mail.thread']
    _description = "Oden de trabajo"
    _order = "ot_number desc"

    #---------------------Basicos----------------------
    def action_autoNum(self): # Genera número consecutivo de NPI
        get_terminado = self.env['dtm.facturado.npi'].search([],order='ot_number desc',limit=1)
        get_npi = self.env['dtm.odt'].search([("tipe_order","=","NPI")],order='ot_number desc', limit=1)
        return get_npi.ot_number + 1 if get_npi.ot_number > get_terminado.ot_number else get_terminado.ot_number + 1

    ot_number = fields.Integer(string="NO.",default=action_autoNum,readonly=True)
    tipe_order = fields.Char(string="TIPO",readonly=True, default='NPI')
    name_client = fields.Char(string="CLIENTE")
    product_name = fields.Char(string="NOMBRE DEL PRODUCTO")
    date_in = fields.Date(string="FECHA DE ENTRADA", default= datetime.today(),readonly=True)
    po_number = fields.Char(string="PO/Cot",readonly=True)
    date_rel = fields.Date(string="FECHA DE ENTREGA", default= datetime.today())
    version_ot = fields.Integer(string="VERSIÓN OT",default=1)
    color = fields.Char(string="COLOR",default="N/A")
    cuantity = fields.Integer(string="CANTIDAD")
    materials_ids = fields.One2many("dtm.materials.line","model_id",string="Lista")
    disenador = fields.Char("Diseñador")
    firma = fields.Char(string="Firma", readonly = True)
    firma_compras = fields.Char()
    firma_produccion = fields.Char()
    firma_almacen = fields.Char()
    firma_ventas = fields.Char(string="Aprobado",readonly=True)
    firma_calidad = fields.Char()
    firma_ingenieria = fields.Char(string="Ingenieria", readonly = True)
    po_fecha_creacion = fields.Date(string="Creación PO", readonly=True)
    po_fecha = fields.Date(string="Fecha PO", readonly=True)
    planos = fields.Boolean(string="Planos",default=False)
    nesteos = fields.Boolean(string="Nesteos",default=False)

    rechazo_id = fields.One2many("dtm.odt.rechazo", "model_id")
    anexos_id = fields.Many2many("ir.attachment" ,"anexos_id",string="Archivos")
    cortadora_id = fields.Many2many("ir.attachment", "cortadora_id",string="Segundas piezas")
    primera_pieza_id = fields.Many2many("ir.attachment", "primera_pieza_id",string="Primeras piezas")
    tubos_id = fields.Many2many("ir.attachment", "tubos_id")
    no_cotizacion = fields.Char('')
    orden_compra_pdf = fields.Many2many("ir.attachment",string='File', readonly =True)
    ligas_id = fields.One2many("dtm.odt.ligas","model_id")
    ligas_tubos_id = fields.One2many("dtm.odt.ligas","model_tubo_id")

    #---------------------Resumen de descripción------------
    description = fields.Text(string="DESCRIPCIÓN")

    #------------------------Notas---------------------------
    notes = fields.Text(string="notes")

    liberado = fields.Char()
    retrabajo = fields.Boolean(default=False) #Al estar en verdadero pone todos los campos en readonly

    maquinados_id = fields.One2many("dtm.odt.servicios","extern_id")



    # ----------------------------------- Funciones ----------------------------------------------------------

    def action_firma_parcial(self):
        self.action_firma(parcial=True)

    def action_firma(self,parcial=False):
        email = self.env.user.partner_id.email
        if email in ['hugo_chacon@dtmindustry.com','ventas1@dtmindustry.com',"rafaguzmang@hotmail.com"] and self.tipe_order != "SK":
            self.firma_ventas = self.env.user.partner_id.name
            self.proceso(parcial)
        else:
            if email in ['ingenieria@dtmindustry.com','ingenieria2@dtmindustry.com',"rafaguzmang@hotmail.com"]:
                self.firma = self.env.user.partner_id.name
            get_ventas = self.env['dtm.compras.items'].search([("orden_trabajo","=",self.ot_number)])
            get_ventas.write({"firma": self.firma})
            if self.firma_ventas and self.tipe_order != "SK":
                self.proceso(parcial)

    def proceso(self,parcial=False):
        get_procesos = self.env['dtm.proceso'].search([("ot_number","=",self.ot_number),("tipe_order","=",self.tipe_order)])
        get_procesos.write({
            "firma_ventas": self.firma_ventas,
            "firma_ventas_kanba":"Ventas"
        })
        get_ot = self.env['dtm.proceso'].search([("ot_number","=",self.ot_number),("tipe_order","=",self.tipe_order)])
        get_almacen = self.env['dtm.almacen.odt'].search([("ot_number","=",self.ot_number)])
        vals = {
                "ot_number":self.ot_number,
                "tipe_order":self.tipe_order,
                "name_client":self.name_client,
                "product_name":self.product_name,
                "date_in":self.date_in,
                "date_rel":self.date_rel,
                "version_ot":self.version_ot,
                "cuantity":self.cuantity,
                "po_number":self.po_number,
                "description":self.description,
                "notes":self.notes,
                "color":self.color
        }
        # Pone en veradero los campos boolean para planos y nesteos
        self.planos = True if self.anexos_id else False
        self.nesteos = True if self.cortadora_id or self.primera_pieza_id else False

        vals["nesteos"] = self.nesteos
        vals["planos"] = self.planos
        vals["firma_parcial"] = parcial
        if get_ot:
            get_ot.write(vals)
            get_ot.write(
                {
                    "firma_diseno":self.firma
                })
        else:
            if not get_ot.status:
                status = "aprobacion"
                if self.cortadora_id or self.primera_pieza_id:
                    status = "corte"
            get_ot.create(vals)
            get_ot = self.env['dtm.proceso'].search([("ot_number","=",self.ot_number),("tipe_order","=",self.tipe_order)])
            get_ot.write(
                {
                    "firma_diseno":self.firma,
                    "status":status
                })
        if get_almacen:
             get_almacen.write({
                "date_in":self.date_in,
                "date_rel":self.date_rel,
                "materials_ids":self.materials_ids
            })
        else:
             # print(self.materials_ids)
             get_almacen.create({
                "ot_number":self.ot_number,
                "tipe_order":self.tipe_order,
                "date_in":self.date_in,
                "date_rel":self.date_rel,
                "materials_ids":self.materials_ids,
            })
        get_ot.materials_ids = self.materials_ids
        get_ot.rechazo_id = self.rechazo_id
        get_ot.write({'anexos_id': [(5, 0, {})]})
        lines = []
        for anexo in self.anexos_id:
            attachment = self.env['ir.attachment'].browse(anexo.id)
            vals = {
                "documentos":attachment.datas,
                "nombre":attachment.name
            }
            get_anexos = self.env['dtm.proceso.anexos'].search([("nombre","=",attachment.name),("documentos","=",attachment.datas)])
            if get_anexos:
                get_anexos.write(vals)
                lines.append(get_anexos.id)
            else:
                get_anexos.create(vals)
                get_anexos = self.env['dtm.proceso.anexos'].search([("nombre","=",attachment.name),("documentos","=",attachment.datas)])
                lines.append(get_anexos.id)
        get_ot.write({'anexos_id': [(6, 0, lines)]})
        lines = []
        get_ot.write({'primera_pieza_id': [(5, 0, {})]})
        if self.primera_pieza_id:
            for anexo in self.primera_pieza_id:
                attachment = self.env['ir.attachment'].browse(anexo.id)
                vals = {
                    "documentos":attachment.datas,
                    "nombre":attachment.name
                }
                get_anexos = self.env['dtm.proceso.primer'].search([("nombre","=",attachment.name),("documentos","=",attachment.datas)])
                if get_anexos:
                    get_anexos.write(vals)
                    lines.append(get_anexos.id)
                else:
                    get_anexos.create(vals)
                    get_anexos = self.env['dtm.proceso.primer'].search([("nombre","=",attachment.name),("documentos","=",attachment.datas)])
                    lines.append(get_anexos.id)
            get_ot.write({'primera_pieza_id': [(6, 0, lines)]})
            lines = []
            get_ot.write({'cortadora_id': [(5, 0, {})]})
            for anexo in self.cortadora_id:
                attachment = self.env['ir.attachment'].browse(anexo.id)
                vals = {
                    "documentos":attachment.datas,
                    "nombre":attachment.name
                }
                get_anexos = self.env['dtm.proceso.cortadora'].search([("nombre","=",attachment.name),("documentos","=",attachment.datas)],order='nombre desc',limit=1)
                if get_anexos:
                    get_anexos.write(vals)
                    lines.append(get_anexos.id)
                else:
                    get_anexos.create(vals)
                    get_anexos = self.env['dtm.proceso.cortadora'].search([("nombre","=",attachment.name),("documentos","=",attachment.datas)],order='nombre desc',limit=1)
                    lines.append(get_anexos.id)
            get_ot.write({'cortadora_id': [(6, 0, lines)]})
        else:
            lines = []
            get_ot.write({'cortadora_id': [(5, 0, {})]})
            for anexo in self.cortadora_id:
                attachment = self.env['ir.attachment'].browse(anexo.id)
                vals = {
                    "documentos":attachment.datas,
                    "nombre":attachment.name
                }
                get_anexos = self.env['dtm.proceso.cortadora'].search([("nombre","=",attachment.name),("documentos","=",attachment.datas)],order='nombre desc',limit=1)
                if get_anexos:
                    get_anexos.write(vals)
                    lines.append(get_anexos.id)
                else:
                    get_anexos.create(vals)
                    get_anexos = self.env['dtm.proceso.cortadora'].search([("nombre","=",attachment.name),("documentos","=",attachment.datas)],order='nombre desc',limit=1)
                    lines.append(get_anexos.id)
            get_ot.write({'cortadora_id': [(6, 0, lines)]})
        # Cortadora laser al modulo proceso
        # Cortadora de tubos al modulo proceso
        get_ot.write({'tubos_id': [(5, 0, {})]})
        lines = []
        for anexo in self.tubos_id:
            attachment = self.env['ir.attachment'].browse(anexo.id)
            vals = {
                "documentos":attachment.datas,
                "nombre":attachment.name,
            }
            get_anexos = self.env['dtm.proceso.tubos'].search([("nombre","=",attachment.name),("documentos","=",attachment.datas)],order='nombre desc',limit=1)
            if get_anexos:
                get_anexos.write(vals)
                lines.append(get_anexos.id)
            else:
                get_anexos.create(vals)
                get_anexos = self.env['dtm.proceso.tubos'].search([("nombre","=",attachment.name),("documentos","=",attachment.datas)],order='nombre desc',limit=1)
                lines.append(get_anexos.id)
        get_ot.write({'tubos_id': [(6, 0, lines)]})
        email = self.env.user.partner_id.email
        self.compras_odt(self.materials_ids,1)
        self.compras_servicios()
        if email in ['ingenieria1@dtmindustry.com','rafaguzmang@hotmail.com']:
            # print("email",email)
            self.firma_ingenieria = self.env.user.partner_id.name
            self.cortadora_laser()
            self.cortadora_tubos()

            # if not parcial:
            #     self.retrabajo = True

    def cortadora_laser(self):
        # print("cortadora_laser",self.cortadora_id,self.primera_pieza_id)
        if self.cortadora_id or self.primera_pieza_id:
            get_proceso = self.env['dtm.proceso'].search([('ot_number','=',self.ot_number),('tipe_order','=',self.tipe_order)])
            get_proceso.status == "aprobacion" and get_proceso.write({'status':"corte"})
            status = get_proceso.mapped('status')
            # print(get_proceso.status,status)
            vals = {
                "orden_trabajo":self.ot_number,
                "fecha_entrada": datetime.today(),
                "nombre_orden":self.product_name,
                "tipo_orden": self.tipe_order
            }
            material_corte = ""
            # Se encargan de buscar la información necesario -------------------------------
            get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=",self.tipe_order)])# Guarda la información (archivos) para pasar a corte
            get_encorte_primera = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=",self.tipe_order),("primera_pieza","=",True)])# Busca si la primera pieza está en proceso de corte
            get_encorte_segunda =  self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=",self.tipe_order),("primera_pieza","=",False)])# Busca si la segunda está en proceso de corte
            get_corte_primer = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=",self.tipe_order),("primera_pieza","=",True)]) # Busca si la primera pieza esta cortada
            get_corte_segunda = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=",self.tipe_order),("primera_pieza","=",False)]) # Busca si las segundas piezas ya fueron cortadas
            #---------------------------------------------------
            # Condicionales
            #    No exite este archivo en ningún modelo de la cortadora, de ser así procede a crearlo
            if not get_encorte_primera and not get_encorte_segunda and not get_corte_primer and not get_corte_segunda:
                # print("primer")
                if self.primera_pieza_id:
                    vals["primera_pieza"]= True
                    get_corte.create(vals) #Crea la orden de primera pieza
                    get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=",self.tipe_order),("primera_pieza","=",True)])# Carga la orden recien creada para su manipulación
                    material_corte = self.primera_pieza_id #Pasa los archivos de la primera pieza
                else:
                    vals["primera_pieza"]= False
                    get_corte.create(vals) #Crea la orden de segunda pieza
                    get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=",self.tipe_order),("primera_pieza","=",False)])# Carga la orden recien creada para su manipulación
                    material_corte = self.cortadora_id # Pasa los archivos de la segunda pieza
            # Si la orden se encuentra en corte actualizará respetando los cortes realizados y agregando los nuevos, no puede quitar cortes realizados
            # elif get_encorte_primera and not get_corte_primer and not get_encorte_segunda and not get_corte_segunda:
            elif get_encorte_primera and not get_corte_primer and not get_encorte_segunda and not get_corte_segunda:
                # print("Primera pieza solo en corte")
                get_corte = get_encorte_primera
                get_corte.write(vals)
                material_corte = self.primera_pieza_id
            elif not get_encorte_primera and get_corte_primer and not get_encorte_segunda and not get_corte_segunda:
                # print("Primera pieza cortada pero no hay segundas piezas")
                if self.primera_pieza_id:
                    vals["primera_pieza"]= True
                    get_corte.create(vals) #Crea la orden de primera pieza
                    material_corte = self.primera_pieza_id
                    get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=",self.tipe_order),("primera_pieza","=",True)])# Carga la orden recien creada para su manipulación
                    get_terminado = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=",self.tipe_order),("primera_pieza","=",True)])
                    if get_terminado:# Si hay archivos cortados los quita del retrabajo
                        record_ids = [] #Almacena los id que serán agregados para ser cortados
                        record_nombres = [] #Lista para llenar con todos los archivos de los documentos cortados
                        for ordenes in get_terminado:#Proceso de busqueda en el modelo de archivos cortados (dtm_laser_realizados)
                            for orden in ordenes:
                                mapa = orden.cortadora_id.mapped("nombre")
                                record_nombres.extend(mapa)
                            # print(record_nombres)
                        for thisFile in self.primera_pieza_id: #Comprara los nuevos archivos con los ya cortados
                            attachment = self.env['ir.attachment'].browse(thisFile.id)
                            if attachment.name in record_nombres:
                                record_nombres.remove(attachment.name)
                            else:
                                record_nombres.append(attachment.name)
                                record_ids.append(attachment.id)
                        recordset = self.env['ir.attachment'].browse(record_ids)
                        material_corte = recordset #Pasa los archivos de la segunda pieza
            elif get_encorte_segunda:#Revisa que la primera pieza sea liberada que primera pieza esté cortada
                #Segunda pieza en corte
                # print("Segunda pieza en corte")
                vals["primera_pieza"]= False
                get_corte = get_encorte_segunda
                get_corte.write(vals)
                material_corte = self.cortadora_id
                get_terminado = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=",self.tipe_order),("primera_pieza","=",False)])
                if get_terminado:# Si hay archivos cortados los quita del retrabajo
                    record_ids = [] #Almacena los id que serán agregados para ser cortados
                    record_nombres = [] #Lista para llenar con todos los archivos de los documentos cortados
                    for ordenes in get_terminado:#Proceso de busqueda en el modelo de archivos cortados (dtm_laser_realizados)
                        for orden in ordenes:
                            mapa = orden.cortadora_id.mapped("nombre")
                            record_nombres.extend(mapa)
                    for thisFile in self.cortadora_id: #Comprara los nuevos archivos con los ya cortados
                        attachment = self.env['ir.attachment'].browse(thisFile.id)
                        if attachment.name in record_nombres:
                            record_nombres.remove(attachment.name)
                        else:
                            record_nombres.append(attachment.name)
                            record_ids.append(attachment.id)
                    recordset = self.env['ir.attachment'].browse(record_ids)
                    material_corte = recordset #Pasa los archivos de la segunda pieza
            elif not get_encorte_segunda and get_corte_segunda:
                # print("Segunda pieza a retrabajo ya con algunas en el status de cortado")
                vals["primera_pieza"]= False
                get_corte.create(vals) #Crea la orden de segunda pieza
                get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=",self.tipe_order),("primera_pieza","=",False)])# Carga la orden recien creada para su manipulación
                material_corte = self.cortadora_id # Pasa los archivos de la segunda pieza
                get_terminado = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=",self.tipe_order),("primera_pieza","=",False)])
                if get_terminado:# Si hay archivos cortados los quita del retrabajo
                    record_ids = [] #Almacena los id que serán agregados para ser cortados
                    record_nombres = [] #Lista para llenar con todos los archivos de los documentos cortados
                    for ordenes in get_terminado:#Proceso de busqueda en el modelo de archivos cortados (dtm_laser_realizados)
                        for orden in ordenes:
                            mapa = orden.cortadora_id.mapped("nombre")
                            record_nombres.extend(mapa)
                    for thisFile in self.cortadora_id: #Comprara los nuevos archivos con los ya cortados
                        attachment = self.env['ir.attachment'].browse(thisFile.id)
                        if attachment.name in record_nombres:
                            record_nombres.remove(attachment.name)
                        else:
                            record_nombres.append(attachment.name)
                            record_ids.append(attachment.id)
                    recordset = self.env['ir.attachment'].browse(record_ids)
                    material_corte = recordset #Pasa los archivos de la segunda pieza
            #-----------------------------------------------------------------------------------------------------------------------


            lines = []
            get_corte.write({'cortadora_id': [(5, 0, {})]})#limpia la tabla de los archivos
            for file in material_corte:
                attachment = self.env['ir.attachment'].browse(file.id)
                vals = {
                    "documentos":attachment.datas,
                    "nombre":attachment.name,
                    "primera_pieza":False
                }
                # if not self.liberado:
                if self.primera_pieza_id and not self.liberado:
                    vals["primera_pieza"] = True
                get_files = self.env['dtm.documentos.cortadora'].search([("nombre","=",file.name)],order='nombre desc',limit=1)
                if get_files:
                    get_files.write(vals)
                    lines.append(get_files.id)
                else:
                    get_files.create(vals)
                    get_files = self.env['dtm.documentos.cortadora'].search([("nombre","=",file.name)],order='nombre desc',limit=1)
                    lines.append(get_files.id)
            get_corte.write({'cortadora_id': [(6, 0, lines)]})

            # Busca todo el material que sea lámina
            lines = []  # Lista para agregar lo ids que serán encontrados
            get_corte.write({"materiales_id":[(5, 0, {})]})#Pasa los materiales correspondientes de la orden
            for lamina in self.materials_ids:
                if re.match("Lámina",lamina.nombre): # Revisa si el material tiene la palabra lámina de no ser así lo descarta
                    get_almacen = self.env['dtm.materiales'].search([("codigo","=",lamina.materials_list.id)]) # Busca el material en el almacén por codigo
                    localizacion = ""
                    if get_almacen.localizacion:  # Si tiene localización la asigna
                        localizacion = get_almacen.localizacion
                    content = { # Valores a sobreescribir o a crear
                        "identificador": lamina.materials_list.id,
                        "nombre": lamina.nombre,
                        "medida": lamina.medida,
                        "cantidad": lamina.materials_cuantity,
                        "inventario": lamina.materials_inventory,
                        "requerido": lamina.materials_required,
                        "localizacion": localizacion
                    }
                    get_cortadora_laminas = self.env['dtm.cortadora.laminas'].search([
                        ("identificador","=",lamina.materials_list.id),("nombre","=",lamina.nombre),
                        ("medida","=",lamina.medida),("cantidad","=",lamina.materials_cuantity),
                        ("inventario","=",lamina.materials_inventory),("requerido","=",lamina.materials_required),
                        ("localizacion","=",localizacion)]) # Busca si exite el material
                    if get_cortadora_laminas: # Si existe lo actualiza
                        get_cortadora_laminas.write(content)
                        lines.append(get_cortadora_laminas.id) # Agrega el id a la lista
                    else:  # Si no existe lo crea
                        get_cortadora_laminas.create(content)
                        get_cortadora_laminas = self.env['dtm.cortadora.laminas'].search([
                        ("identificador","=",lamina.materials_list.id),("nombre","=",lamina.nombre),
                        ("medida","=",lamina.medida),("cantidad","=",lamina.materials_cuantity),
                        ("inventario","=",lamina.materials_inventory),("requerido","=",lamina.materials_required),
                        ("localizacion","=",localizacion)])
                        lines.append(get_cortadora_laminas.id) # Agrega el id a la lista
            # Busca los material en el modelo dtm.cortes.realizado para quitarlos de lines
            get_lamina_cortadas = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=",self.tipe_order)])#Busca si hay materiales cortados
            if get_lamina_cortadas:
                list_nombre = []
                result = []
                for ordenes in get_lamina_cortadas:
                    for orden in ordenes:
                        mapa = orden.materiales_id.mapped("id")
                        list_nombre.extend(mapa)
                for line in lines: #Revisa todos los ids de la lista() lines y si alguno ya fué cortado (dtm_laser_realizados) lo elimina de la lista
                    if not line in list_nombre:
                        result.append(line)
                lines = result
            get_corte.write({"materiales_id":[(6, 0,lines)]})
            self.retrabajo = False

    def cortadora_tubos(self):
        if self.tubos_id: #Agrega los datos a la máquina de corte
            vals = {
                "orden_trabajo":self.ot_number,
                "fecha_entrada": datetime.today(),
                "nombre_orden":self.product_name,
                "tipo_orden": self.tipe_order
            }
            get_corte = self.env['dtm.tubos.corte'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=",self.tipe_order)])
            # get_corte_realizado = self.env['dtm.tubos.realizados'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=",self.tipe_order)])
            # if not get_corte_realizado:
            if get_corte:
                get_corte.write(vals)
            else:
                get_corte.create(vals)
                get_corte = self.env['dtm.tubos.corte'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=",self.tipe_order)])

            lines = []
            get_corte.write({'cortadora_id': [(5, 0, {})]})
            for file in self.tubos_id:
                attachment = self.env['ir.attachment'].browse(file.id)
                vals = {
                    "documentos":attachment.datas,
                    "nombre":attachment.name,
                }
                get_files = self.env['dtm.tubos.documentos'].search([("nombre","=",file.name),("documentos","=",attachment.datas)], order='id desc',limit=1)
                if get_files:
                    get_files.write(vals)
                    lines.append(get_files.id)
                else:
                    get_files.create(vals)
                    get_files = self.env['dtm.tubos.documentos'].search([("nombre","=",file.name),("documentos","=",attachment.datas)], order='id desc',limit=1)
                    lines.append(get_files.id)
            get_corte.write({'cortadora_id': [(6, 0, lines)]})

            lines = []
            get_corte.write({"materiales_id":[(5, 0, {})]})
            for material in self.materials_ids: # Busca que coincidan el nombre del material para la busqueda de codigo en su respectivo modelo
                get_almacen = self.env['dtm.materiales.solera'].search([("codigo","=","0")])
                if re.match("Solera",material.nombre):
                    get_almacen = self.env['dtm.materiales.solera'].search([("codigo","=",material.materials_list.id)])
                elif re.match("Ángulo",material.nombre):
                    get_almacen = self.env['dtm.materiales.angulos'].search([("codigo","=",material.materials_list.id)])
                elif re.match("Perfil",material.nombre):
                    get_almacen = self.env['dtm.materiales.perfiles'].search([("codigo","=",material.materials_list.id)])
                elif re.match("Canal",material.nombre):
                    get_almacen = self.env['dtm.materiales.canal'].search([("codigo","=",material.materials_list.id)])
                elif re.match("Tubo",material.nombre):
                    get_almacen = self.env['dtm.materiales.tubos'].search([("codigo","=",material.materials_list.id)])
                # elif re.match("IPR",material.nombre):
                #     get_almacen = self.env['dtm.materiales.angulos'].search([("codigo","=",material.materials_list.id)])

                if get_almacen:
                    localizacion = ""
                    if get_almacen.localizacion:
                        localizacion = get_almacen.localizacion
                    content = {
                        "identificador": material.materials_list.id,
                        "nombre": material.nombre,
                        "medida": material.medida,
                        "cantidad": material.materials_cuantity,
                        "inventario": material.materials_inventory,
                        "requerido": material.materials_required,
                        "localizacion": localizacion
                    }
                    get_cortadora_laminas = self.env['dtm.tubos.materiales'].search([
                        ("identificador","=",material.materials_list.id),("nombre","=",material.nombre),
                        ("medida","=",material.medida),("cantidad","=",material.materials_cuantity),
                        ("inventario","=",material.materials_inventory),("requerido","=",material.materials_required),
                        ("localizacion","=",localizacion)])
                    if get_cortadora_laminas:
                        get_cortadora_laminas.write(content)
                        lines.append(get_cortadora_laminas.id)
                    else:
                        get_cortadora_laminas.create(content)
                        get_cortadora_laminas = self.env['dtm.tubos.materiales'].search([
                        ("identificador","=",material.materials_list.id),("nombre","=",material.nombre),
                        ("medida","=",material.medida),("cantidad","=",material.materials_cuantity),
                        ("inventario","=",material.materials_inventory),("requerido","=",material.materials_required),
                        ("localizacion","=",localizacion)])
                        lines.append(get_cortadora_laminas.id)
                get_corte.write({"materiales_id":[(6, 0,lines)]})

    def compras_odt(self,materiales,ref,servicio=False):
        # ref == 2 and print(materiales,ref)
        # print(materiales.mapped('materials_list.id'))
        for codigo in materiales:
            # Si el item no tiene marcado el check box hace los calculos para el área de compras
            if codigo.revicion:

                # Suma la cantidad requerida con los codigos repetidos dentro de la misma Orden
                cantidad_item = sum(self.env['dtm.materials.line'].search([("model_id","=",self.env['dtm.odt'].search([("ot_number","=",str(self.ot_number))]).id),("materials_list","=",codigo.materials_list.id)]).mapped('materials_required'))
                # cantidad_total = sum(self.env['dtm.materials.line'].search([("model_id","=",self.env['dtm.odt'].search([("ot_number","=",str(self.ot_number))]).id),("materials_list","=",codigo.materials_list.id)]).mapped('materials_'))
                if ref == 2:
                    cantidad_item = self.env['dtm.materials.line'].search([("id","=",codigo.id)]).materials_required
                # ref == 2 and print("Solicitado",cantidad_item)
                # Busca los materiales solicitados en el apartado de requerido
                get_compras = self.env['dtm.compras.requerido'].search([("orden_trabajo","ilike",str(self.ot_number)),("codigo","=",codigo.materials_list.id)], limit=1)
                get_compras_odt = get_compras.mapped('orden_trabajo')
                get_compras_cantidad = get_compras.mapped('cantidad')
                # ref == 2 and print("Codigo",codigo.materials_list.id)
                list_reque_odt = list(set(",".join(get_compras_odt).replace(","," ").split()))
                list_reque_odt = list(filter(lambda x: x!=str(self.ot_number),list_reque_odt))
                total_reque = sum([self.env['dtm.materials.line'].search([("model_id","=",self.env['dtm.odt'].search([("ot_number","=",item)]).id),("materials_list","=",codigo.materials_list.id)]).materials_required for item in list_reque_odt])
                if ref == 2:
                    total_reque = sum([self.env['dtm.materials.line'].search([("id","=",codigo.id)]).materials_required for item in list_reque_odt])
                cantidad_reque = sum(get_compras_cantidad) - total_reque
                # ref == 2 and print("Requerido",cantidad_reque)

                # Busca los materiales solicitados en el apartado de comprado
                get_comprado = self.env['dtm.compras.realizado'].search([("orden_trabajo","ilike",str(self.ot_number)),("codigo","=",codigo.materials_list.id),("comprado","=",False)])
                get_comprado_odt = get_comprado.mapped('orden_trabajo')
                get_comprado_cantidad = get_comprado.mapped('cantidad')
                # ref == 2 and print(get_comprado,get_comprado_odt,get_comprado_cantidad)
                list_comprado_odt = list(set(",".join(get_comprado_odt).replace(","," ").split()))
                # ref == 2 and print(list_comprado_odt)
                list_comprado_odt = list(filter(lambda x: x!=str(self.ot_number),list_comprado_odt))
                # ref == 2 and print(list_comprado_odt)
                total_comprado = sum([self.env['dtm.materials.line'].search([("model_id","=",self.env['dtm.odt'].search([("ot_number","=",item)]).id),("materials_list","=",codigo.materials_list.id)]).materials_required for item in list_comprado_odt])
                if ref == 2:
                    total_comprado = sum([self.env['dtm.materials.line'].search([("id","=",codigo.id)]).materials_required for item in list_comprado_odt])
                # ref == 2 and print("--",sum(get_comprado_cantidad),total_comprado)
                cantidad_comprado = (sum(get_comprado_cantidad) if sum(get_comprado_cantidad) > 0 else 0) - (total_comprado if total_comprado > 0 else 0)
                # ref == 2 and print("Comprado",cantidad_comprado)
                # ref == 2 and print("Comparación",cantidad_item,cantidad_comprado)
                # ref == 2 and print("------------------------------------------------------------------------------------------------------------------------------------------------------")
                # print(codigo.nombre,codigo.materials_list.id,servicio,)
                # print(get_compras.disenador)
                # print(self.firma if not get_compras.disenador else "")
                vals = {
                        'orden_trabajo':self.ot_number,
                        'codigo':codigo.materials_list.id,
                        'nombre':f"{codigo.nombre} {codigo.medida if codigo.medida else ''}",
                        'cantidad':cantidad_item - cantidad_comprado,
                        'disenador':self.env.user.partner_id.name,
                        'servicio':servicio
                    }
                if get_compras.disenador:
                    vals['disenador'] = get_compras.disenador
                get_compras = self.env['dtm.compras.requerido'].search([("orden_trabajo","=",str(self.ot_number)),("codigo","=",codigo.materials_list.id)])
                # Si la cantidad requerida no ha sido comprada la crea o la actualiza
                if not get_comprado and codigo.materials_required > 0:
                    get_compras.write(vals) if get_compras else get_compras.create(vals)
                # Si la cantidad requerida es mayor a la comprada crea una nueva compra o la actualiza
                elif cantidad_item > cantidad_comprado and codigo.materials_required > 0:
                    get_compras.write(vals) if get_compras else get_compras.create(vals)
                # Si la cantidad requerida es igual a la comprada y se había generado un nueva orden de compra esta sera borrada
                elif cantidad_item == cantidad_comprado:
                    get_compras.unlink()
                # Si este item requiere cero esta será borrada
                if codigo.materials_required <= 0 and get_compras:
                    get_compras.unlink()

    def compras_servicios(self):
        get_servicios = self.env['dtm.compras.servicios'].search([("numero_orden","=",self.ot_number),("tipo_orden","=",self.tipe_order)])
        if self.maquinados_id:
            for servicio in self.maquinados_id:
                vals = {
                    "nombre": servicio.nombre,
                    "cantidad": servicio.cantidad,
                    "tipo_orden": self.tipe_order,
                    "numero_orden": self.ot_number,
                    "proveedor": servicio.proveedor,
                    "fecha_solicitud": servicio.fecha_solicitud,
                    "fecha_compra": servicio.fecha_compra,
                    "fecha_entrada": servicio.fecha_entrada,
                    "material_id": servicio.material_id,
                    "anexos_id": servicio.anexos_id
                }
                get_servicios.write(vals) if get_servicios else get_servicios.create(vals)
                self.compras_odt(servicio.material_id,2,True)

    @api.onchange("maquinados_id")
    def _onchange_maquinados_id(self):
        for item in self.maquinados_id:
            nombre = f"Maquinado {item.nombre}"
            get_almacen = self.env['dtm.diseno.almacen'].search([("nombre","=",nombre)],limit=1)
            get_almacen.write({"nombre": nombre}) if get_almacen else get_almacen.create({"nombre": nombre})
            get_almacen = self.env['dtm.diseno.almacen'].search([("nombre","=",nombre)],limit=1)

            get_materials = self.env['dtm.materials.line'].search([("model_id","=",self.id),("nombre","=",f"Maquinado {item.nombre}")])
            vals = {
                "model_id":self.id,
                "nombre":nombre,
                "medida": "",
                "materials_list":get_almacen.id,
                "materials_list":get_almacen.id,
                "materials_cuantity":item.cantidad,
            }
            get_materials.write(vals) if f"Maquinado {item.nombre}" in self.materials_ids.mapped('nombre') else get_materials.create(vals)


# --------------------------------- Botones del header ----------------------------------------------

    def action_imprimir_formato(self): # Imprime según el formato que se esté llenando
        return self.env.ref("dtm_odt.formato_orden_de_trabajo").report_action(self)

    def action_imprimir_materiales(self): # Imprime según el formato que se esté llenando
        return self.env.ref("dtm_odt.formato_lista_materiales").report_action(self)

#--------------------------------------- Get View -----------------------------------------------------

    # def get_view(self, view_id=None, view_type='form', **options):
    #     res = super(DtmOdt,self).get_view(view_id, view_type,**options)
    #
    #     get_self = self.env['dtm.odt'].search([])
    #
    #     for get in get_self:
    #         get_po_file = self.env['dtm.ordenes.compra'].search([('orden_compra','=',get.po_number)])
    #         if get_po_file and get.tipe_order != "SK":
    #             get_po_ir = self.env['ir.attachment'].browse(get_po_file.archivos_id.id)
    #             get_anex_ir = self.env['ir.attachment'].browse(get_po_file.anexos_id)
    #
    #             lines = []
    #             if get_po_ir:#Agrega archivo pdf de la po
    #                 lines.extend(self.env['ir.attachment'].browse(get_po_file.archivos_id.id).mapped("id"))
    #             if get_anex_ir:#Agrega archivos anexos
    #                 for anexo in get_anex_ir:
    #                     lines.append(anexo.id.id)
    #             if lines:
    #                 get.write({'orden_compra_pdf': [(5, 0, {})]})
    #                 get.write({'orden_compra_pdf': [(6, 0, lines)]})
    #
    #             #Agrega fechas importantes de la PO
    #             get.write({"po_fecha_creacion":get_po_file.fecha_captura_po,
    #                        "po_fecha":get_po_file.fecha_po})
    #
    #
    #
    #     return res


    #-----------------------Materiales----------------------

class TestModelLine(models.Model):
    _name = "dtm.materials.line"
    _description = "Tabla de materiales"

    model_id = fields.Many2one("dtm.odt")
    servicio_id = fields.Many2one("dtm.odt.servicios")
    nombre = fields.Char(compute="_compute_material_list",store=True)
    medida = fields.Char(store=True)

    materials_list = fields.Many2one("dtm.diseno.almacen", string="LISTADO DE MATERIALES",required=True)
    materials_cuantity = fields.Integer("CANTIDAD")
    materials_inventory = fields.Integer("INVENTARIO", readonly=True)
    materials_availabe = fields.Integer("APARTADO", readonly=True)
    materials_required = fields.Integer("REQUERIDO",compute ="_compute_materials_inventory",store=True)
    revicion = fields.Boolean(string="COMPRAR")

    @api.depends("materials_cuantity")
    def _compute_materials_inventory(self):
        for result in self:
            result.materials_required = 0
            get_almacen = result.env['dtm.diseno.almacen'].search([("id","=",result.materials_list.id)])#Obtiene la información por medio del id del item seleccionado
            result.materials_inventory = get_almacen.cantidad# Siempre será el valor dado por la consulta de almacén
            result.materials_availabe = result.materials_cuantity if result.materials_cuantity <= get_almacen.disponible else get_almacen.disponible
            result.materials_required = result.materials_cuantity - result.materials_availabe
            if result.materials_cuantity < 0:
                result.materials_cuantity = 0
            if result.materials_availabe < 0:
                result.materials_availabe = 0
            #Revisa las ordenes que contengan este material y que este apartado
            #Se revisa el material en diseño únicamente en ordenes no autorizadas por el área de ventas
            get_odt = self.env['dtm.odt'].search([("firma_ventas","=",False)]).mapped('id')
            get_odt_codigo = list(filter(lambda id: self.env['dtm.materials.line'].search([("model_id","=",id),("materials_list","=",self.materials_list.id)]),get_odt))
            get_proceso = self.env['dtm.proceso'].search(["|",("status","=","aprobacion"),("status","=","corte")]).mapped('id')
            get_proceso_codigo = list(filter(lambda id: self.env['dtm.materials.line'].search([("model_id","=",id),("materials_list","=",self.materials_list.id)]),get_proceso))
            # Es la suma de todas las ordenes donde se encuentra este item
            list_search = []
            # Guarda el id de las ordenes que contiene el item
            list_search.extend(get_odt_codigo)
            list_search.extend(get_proceso_codigo)
            cont = 0
            suma = sum([self.env['dtm.materials.line'].search([("model_id","=",item),("materials_list","=",self.materials_list.id)]).materials_cuantity for item in list_search])
            get_almacen.write({
                "apartado": get_almacen.cantidad if suma > get_almacen.cantidad else suma,
                "disponible":get_almacen.cantidad - suma if get_almacen.cantidad - suma > 0 else 0
            })


    @api.depends("materials_list")
    def _compute_material_list(self):
        for result in self:
            result.nombre = result.materials_list.nombre
            result.medida = result.materials_list.medida

class Rechazo(models.Model):
    _name = "dtm.odt.rechazo"
    _description = "Tabla para llenar los motivos por el cual se rechazo la ODT"

    model_id = fields.Many2one("dtm.odt")

    descripcion = fields.Text(string="Descripción del Rechazo")
    fecha = fields.Date(string="Fecha")
    hora = fields.Char(string="Hora")
    firma = fields.Char(string="Firma", default="Diseño")

    @api.onchange("fecha")
    def _action_fecha(self):
        self.fecha = datetime.now()

        self.hora = datetime.now(pytz.timezone('America/Mexico_City')).strftime("%H:%M")

class Servicios(models.Model):
    _name = "dtm.odt.servicios"
    _description = "Modelo para la solicitud de servicios externos"

    extern_id = fields.Many2one("dtm.odt")

    nombre = fields.Char(string="Nombre del Servicio")
    cantidad = fields.Integer(string="Cantidad")
    tipo_orden = fields.Char(string="OT/NPI")
    numero_orden = fields.Integer(string="Orden")
    proveedor = fields.Char(string="Proveedor",readonly=True)
    fecha_solicitud = fields.Date(string="Fecha de Solicitud", default= datetime.today(),readonly=True)
    fecha_compra = fields.Date(string="Fecha de Compra",readonly=True)
    fecha_entrada = fields.Date(string="Fecha de Entrada",readonly=True)
    material_id = fields.One2many("dtm.materials.line","servicio_id")
    anexos_id = fields.Many2many("ir.attachment")

class OtFile(models.Model):
    _name="dtm.odt.ligas"
    _description = "Modelo para almacenar el archivo de las ligas para el admin"
    model_id = fields.Many2one("dtm.odt")
    model_tubo_id = fields.Many2one("dtm.odt")
    liga = fields.Char(string="Ligas")








