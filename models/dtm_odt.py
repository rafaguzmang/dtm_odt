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

    ot_number = fields.Integer(string="NÚMERO",readonly=True)
    tipe_order = fields.Char(string="TIPO",readonly=True)
    name_client = fields.Char(string="CLIENTE",readonly=True)
    product_name = fields.Char(string="NOMBRE DEL PRODUCTO",readonly=True)
    date_in = fields.Date(string="FECHA DE ENTRADA", default= datetime.today(),readonly=True)
    po_number = fields.Char(string="PO",readonly=True)
    date_rel = fields.Date(string="FECHA DE ENTREGA", default= datetime.today())
    version_ot = fields.Integer(string="VERSIÓN OT",default=1)
    color = fields.Char(string="COLOR",default="N/A")
    cuantity = fields.Integer(string="CANTIDAD",readonly=True)
    materials_ids = fields.One2many("dtm.materials.line","model_id",string="Lista")
    disenador = fields.Char("Diseñador")
    firma = fields.Char(string="Firma", readonly = True)
    firma_compras = fields.Char()
    firma_produccion = fields.Char()
    firma_almacen = fields.Char()
    firma_ventas = fields.Char(string="Aprobado",readonly=True)
    firma_calidad = fields.Char()

    planos = fields.Boolean(string="Planos",default=False)
    nesteos = fields.Boolean(string="Nesteos",default=False)

    rechazo_id = fields.One2many("dtm.odt.rechazo", "model_id")
    anexos_id = fields.Many2many("ir.attachment" ,"anexos_id",string="Archivos")
    cortadora_id = fields.Many2many("ir.attachment", "cortadora_id",string="Segundas piezas")
    primera_pieza_id = fields.Many2many("ir.attachment", "primera_pieza_id",string="Primeras piezas")
    tubos_id = fields.Many2many("ir.attachment", "tubos_id")
    no_cotizacion = fields.Char('')

    #---------------------Resumen de descripción------------
    description = fields.Text(string="DESCRIPCIÓN")

    #------------------------Notas---------------------------
    notes = fields.Text(string="notes")

    liberado = fields.Char()
    retrabajo = fields.Boolean(default=False) #Al estar en verdadero pone todos los campos en readonly

    maquinados_id = fields.One2many("dtm.odt.sercicios","extern_id")

    # @api.onchange('maquinados_id')
    # def _onchange_maquinados_id(self):
    #     if self.maquinados_id:
    #         for record in self.maquinados_id:
    #             # Alguna lógica aquí
    #             pass

    def action_firma_parcial(self):
        self.action_firma(parcial=True)

    def action_firma(self,parcial=False):
        email = self.env.user.partner_id.email
        if not parcial:
            self.retrabajo = True
        if email == 'hugo_chacon@dtmindustry.com'or email=='ventas1@dtmindustry.com' or email=="rafaguzmang@hotmail.com":
            self.firma_ventas = self.env.user.partner_id.name
            self.proceso(parcial)
            # get_items = self.env['dtm.compras.items'].search([("orden_trabajo","=",self.ot_number)])
        else:
            self.firma = self.env.user.partner_id.name
            get_ventas = self.env['dtm.compras.items'].search([("orden_trabajo","=",self.ot_number)])
            get_ventas.write({"firma": self.firma})
            if self.firma_ventas:
                self.proceso(parcial)

        # get_compras = self.env['dtm.ordenes.compra'].search([("no_cotizacion","=",self.no_cotizacion)])
        # get_compras.write({"status":"Procesos"})
        # for orden in get_compras.descripcion_id:
        #     if not orden.firma:
        #         get_compras.write({"status":"Diseño"})
        #         break

    def proceso(self,parcial=False):
        get_procesos = self.env['dtm.proceso'].search([("ot_number","=",self.ot_number),("tipe_order","=","OT")])
        get_procesos.write({
            "firma_ventas": self.firma_ventas,
            "firma_ventas_kanba":"Ventas"
        })
        get_ot = self.env['dtm.proceso'].search([("ot_number","=",self.ot_number),("tipe_order","=","OT")])
        get_almacen = self.env['dtm.almacen.odt'].search([("ot_number","=",self.ot_number)])
        vals = {
                "ot_number":self.ot_number,
                "tipe_order":"OT",
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
        self.planos = False
        self.nesteos = False
        if self.anexos_id:
            self.planos = True
        if self.cortadora_id or self.primera_pieza_id:
            self.nesteos = True
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
            get_ot = self.env['dtm.proceso'].search([("ot_number","=",self.ot_number),("tipe_order","=","OT")])
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
        self.cortadora_laser()
        self.cortadora_tubos()
        self.compras_odt()

    def cortadora_laser(self):
        vals = {
            "orden_trabajo":self.ot_number,
            "fecha_entrada": datetime.today(),
            "nombre_orden":self.product_name,
            "tipo_orden": "OT"
        }
        material_corte = ""
        # Se encargan de buscar la información necesario -------------------------------
        get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT")])# Guarda la información (archivos) para pasar a corte
        get_encorte_primera = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT"),("primera_pieza","=",True)])# Busca si la primera pieza está en proceso de corte
        get_encorte_segunda =  self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT"),("primera_pieza","=",False)])# Busca si la segunda está en proceso de corte
        get_corte_primer = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT"),("primera_pieza","=",True)]) # Busca si la primera pieza esta cortada
        get_corte_segunda = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT"),("primera_pieza","=",False)]) # Busca si las segundas piezas ya fueron cortadas
        #---------------------------------------------------
        # Condicionales
        #    No exite este archivo en ningún modelo de la cortadora, de ser así procede a crearlo
        if not get_encorte_primera and not get_encorte_segunda and not get_corte_primer and not get_corte_segunda:
            # print("primer")
            if self.primera_pieza_id:
                vals["primera_pieza"]= True
                get_corte.create(vals) #Crea la orden de primera pieza
                get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT"),("primera_pieza","=",True)])# Carga la orden recien creada para su manipulación
                material_corte = self.primera_pieza_id #Pasa los archivos de la primera pieza
            else:
                vals["primera_pieza"]= False
                get_corte.create(vals) #Crea la orden de segunda pieza
                get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT"),("primera_pieza","=",False)])# Carga la orden recien creada para su manipulación
                material_corte = self.cortadora_id # Pasa los archivos de la segunda pieza
        # Si la orden se encuentra en corte actualizará respetando los cortes realizados y agregando los nuevos, no puede quitar cortes realizados
        # elif get_encorte_primera and not get_corte_primer and not get_encorte_segunda and not get_corte_segunda:
        elif get_encorte_primera and not get_corte_primer and not get_encorte_segunda and not get_corte_segunda:
            print("Primera pieza solo en corte")
            get_corte = get_encorte_primera
            get_corte.write(vals)
            material_corte = self.primera_pieza_id
        elif not get_encorte_primera and get_corte_primer and not get_encorte_segunda and not get_corte_segunda:
            print("Primera pieza cortada pero no hay segundas piezas")
            if self.primera_pieza_id:
                vals["primera_pieza"]= True
                get_corte.create(vals) #Crea la orden de primera pieza
                material_corte = self.primera_pieza_id
                get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT"),("primera_pieza","=",True)])# Carga la orden recien creada para su manipulación
                get_terminado = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT"),("primera_pieza","=",True)])
                if get_terminado:# Si hay archivos cortados los quita del retrabajo
                    record_ids = [] #Almacena los id que serán agregados para ser cortados
                    record_nombres = [] #Lista para llenar con todos los archivos de los documentos cortados
                    for ordenes in get_terminado:#Proceso de busqueda en el modelo de archivos cortados (dtm_laser_realizados)
                        for orden in ordenes:
                            mapa = orden.cortadora_id.mapped("nombre")
                            record_nombres.extend(mapa)
                        print(record_nombres)
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
            get_terminado = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT"),("primera_pieza","=",False)])
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
            get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT"),("primera_pieza","=",False)])# Carga la orden recien creada para su manipulación
            material_corte = self.cortadora_id # Pasa los archivos de la segunda pieza
            get_terminado = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT"),("primera_pieza","=",False)])
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
                "tipo_orden": "OT"
            }
            get_corte = self.env['dtm.tubos.corte'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT")])
            # get_corte_realizado = self.env['dtm.tubos.realizados'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT")])
            # if not get_corte_realizado:
            if get_corte:
                get_corte.write(vals)
            else:
                get_corte.create(vals)
                get_corte = self.env['dtm.tubos.corte'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT")])

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

    def compras_odt(self):
        get_compras = self.env['dtm.compras.requerido'].search([("orden_trabajo","=",str(self.ot_number))])
        get_realizado = self.env['dtm.compras.realizado'].search([("orden_trabajo","=",str(self.ot_number))])
        if self.materials_ids:# si la orden contiene materiales ejecuta el código
            for compra in get_compras:#Borra los materiales que esten en compras pero no en la orden
                contiene = False
                for material in self.materials_ids:
                    # print(material.materials_list.id,compra.codigo)
                    if material.materials_list.id == compra.codigo:
                        contiene = True
                if not contiene:
                    compra.unlink()
            mapMaterial = {}
            for material in self.materials_ids:
                if not mapMaterial.get(material.materials_list.id):
                    mapMaterial[material.materials_list.id] = material.materials_required
                else:
                    mapMaterial[material.materials_list.id] = mapMaterial.get(material.materials_list.id) + material.materials_required
            mapCompras = {}
            for material in get_compras:
                if not mapCompras.get(material.codigo):
                    mapCompras[material.codigo] = material.cantidad
                else:
                    mapCompras[material.codigo] = mapCompras.get(material.codigo) + material.cantidad

            for material in get_realizado:
                if not mapCompras.get(material.codigo):
                    mapCompras[material.codigo] = material.cantidad
                else:
                    mapCompras[material.codigo] = mapCompras.get(material.codigo) + material.cantidad

            for material in self.materials_ids:
                medida = ""
                requeridoCompras = 0
                requeridoDiseno = 0
                if material.medida: #Quita falso al valor medida
                    medida = material.medida
                if mapCompras.get(material.materials_list.id):
                    requeridoCompras = mapCompras.get(material.materials_list.id) #Requerido de compras
                if mapMaterial.get(material.materials_list.id): #Requerido de diseño
                    requeridoDiseno = mapMaterial.get(material.materials_list.id)

                if requeridoDiseno > requeridoCompras:
                    cantidad = requeridoDiseno
                else:
                    cantidad = 0
                # print(material.nombre,cantidad)
                if cantidad > 0:
                    vals = {
                        "orden_trabajo":self.ot_number,
                        "codigo":material.materials_list.id,
                        "nombre":material.nombre + medida,
                        "cantidad":cantidad,
                        "disenador":self.firma
                    }
                    get_compras_item = self.env['dtm.compras.requerido'].search([("orden_trabajo","=",str(self.ot_number)),("codigo","=",material.materials_list.id)])
                    if get_compras_item:
                        get_compras_item.write(vals)
                    else:
                        get_compras_item.create(vals)
        else:
            get_compras.unlink()

    def action_imprimir_formato(self): # Imprime según el formato que se esté llenando
        return self.env.ref("dtm_odt.formato_orden_de_trabajo").report_action(self)

    def action_imprimir_materiales(self): # Imprime según el formato que se esté llenando
        return self.env.ref("dtm_odt.formato_lista_materiales").report_action(self)

    # def get_view(self, view_id=None, view_type='form', **options):
    #     res = super(DtmOdt,self).get_view(view_id, view_type,**options)
    #     get_almdis = self.env['dtm.diseno.almacen'].search([])
    #
    #     for lamina in get_almdis:
    #         if lamina.nombre.rfind("Lámina") >= 0:
    #             get_ot = self.env['dtm.materials.line'].search([("materials_list","=",lamina.id)])
    #             get_npi = self.env['dtm.materials.npi'].search([("materials_list","=",lamina.id)])
    #             get_lamina = self.env['dtm.materiales'].search([("codigo","=",lamina.id)])
    #
    #             if not get_ot and  not get_npi and not get_lamina:
    #                 print(lamina.id)
    #                 lamina.unlink()
    #
    #             if get_ot or get_npi and not get_lamina:
    #                 print(lamina.id)
    #                 lamina.write({"no_almacen":True})
    #
    #     # for material in get_almdis:
    #     #     get_ot = self.env['dtm.materials.line'].search([("materials_list","=",material.id)])
    #     #     get_npi = self.env['dtm.materials.npi'].search([("materials_list","=",material.id)])
    #     #     # get_lamina = self.env['dtm.materiales'].search([()])
    #     #
    #     #     if not get_ot and  not get_npi:
    #     #         print(material.id)
    #     #         material.unlink()
    #
    #
    #     # attachments = self.env['ir.attachment'].search([])
    #     # for attachment in attachments:
    #     #     if attachment and attachment.store_fname and isinstance(attachment.store_fname, str):
    #     #         if not os.path.exists(attachment._full_path(attachment.store_fname)):
    #     #             print(f"Archivo faltante: {attachment.store_fname} para {attachment.name}",attachment.id)
    #     #             attachment.unlink()
    #     # self.env['ir.cache'].clear()
    #
    #     return res


    #-----------------------Materiales----------------------

class TestModelLine(models.Model):
    _name = "dtm.materials.line"
    _description = "Tabla de materiales"

    model_id = fields.Many2one("dtm.odt")
    model_servicio_id = fields.Many2one("dtm.odt.sercicios")

    nombre = fields.Char(compute="_compute_material_list",store=True)
    medida = fields.Char(store=True)

    materials_list = fields.Many2one("dtm.diseno.almacen", string="LISTADO DE MATERIALES",required=True)
    materials_cuantity = fields.Integer("CANTIDAD")
    materials_inventory = fields.Integer("INVENTARIO", readonly=True)
    materials_availabe = fields.Integer("APARTADO", readonly=True)
    materials_required = fields.Integer("REQUERIDO",compute ="_compute_materials_inventory",store=True)

    def action_materials_list(self):
        pass

    def consultaAlmacen(self,nombre,codigo):
         get_almacen =  self.env['dtm.materiales.otros'].search([("codigo", "=", codigo)])
         if get_almacen:
             return get_almacen
         if nombre:
             if re.match(".*[Ll][aáAÁ][mM][iI][nN][aA].*",nombre):
                get_almacen = self.env['dtm.materiales'].search([("codigo","=",codigo)])
             elif re.match(".*[aáAÁ][nN][gG][uU][lL][oO][sS]*.*",nombre):
                get_almacen = self.env['dtm.materiales.angulos'].search([("codigo","=",codigo)])
             elif re.match(".*[cC][aA][nN][aA][lL].*",nombre):
                get_almacen = self.env['dtm.materiales.canal'].search([("codigo","=",codigo)])
             elif re.match(".*[pP][eE][rR][fF][iI][lL].*",nombre):
                get_almacen = self.env['dtm.materiales.perfiles'].search([("codigo","=",codigo)])
             elif re.match(".*[pP][iI][nN][tT][uU][rR][aA].*",nombre):
                get_almacen = self.env['dtm.materiales.pintura'].search([("codigo","=",codigo)])
             elif re.match(".*[Rr][oO][dD][aA][mM][iI][eE][nN][tT][oO].*",nombre):
                get_almacen = self.env['dtm.materiales.rodamientos'].search([("codigo","=",codigo)])
             elif re.match(".*[tT][oO][rR][nN][iI][lL][lL][oO].*",nombre):
                get_almacen = self.env['dtm.materiales.tornillos'].search([("codigo","=",codigo)])
             elif re.match(".*[tT][uU][bB][oO].*",nombre):
                get_almacen = self.env['dtm.materiales.tubos'].search([("codigo","=",codigo)])
             elif re.match(".*[vV][aA][rR][iI][lL][lL][aA].*",nombre):
                get_almacen = self.env['dtm.materiales.varilla'].search([("codigo","=",codigo)])
             elif re.match(".*[sS][oO][lL][eE][rR][aA].*",nombre):
                get_almacen = self.env['dtm.materiales.solera'].search([("codigo","=",codigo)])
             if len(get_almacen) > 1:
                raise ValidationError("Codigo duplicado, favor de borrar desde Almacén.")
         return  get_almacen

    @api.depends("materials_cuantity")
    def _compute_materials_inventory(self):
        for result in self:
            result.materials_required = 0
            consulta  = result.consultaAlmacen(result.nombre,result.materials_list.id)
            if consulta:
                self.materials_inventory = consulta.cantidad# Siempre será el valor dado por la consulta de almacén
                self.materials_availabe = self.materials_cuantity if self.materials_cuantity <= consulta.disponible else consulta.disponible
                self.materials_required = self.materials_cuantity - self.materials_availabe
                if self.materials_cuantity < 0:
                    self.materials_cuantity = 0
                if self.materials_availabe < 0:
                    self.materials_availabe = 0
                #Revisa las ordenes que contengan este material y que este apartado
                #Se revisa el material en diseño únicamente en ordenes no autorizadas por el área de ventas
                get_odt = self.env['dtm.odt'].search([("firma_ventas","=",False)])
                get_npi = self.env['dtm.npi'].search([("firma_ventas","=",False)])
                get_proceso = self.env['dtm.proceso'].search(["|",("status","=","aprobacion"),("status","=","corte")])
                get_proceso_npi = self.env['dtm.proceso'].search(["|",("status","=","aprobacion"),("status","=","corte")])
                list_search = [get_odt,get_npi,get_proceso,get_proceso_npi]
                cont = 0
                suma = 0
                for search in list_search:
                    list_materiales = search.materials_ids if cont == 0 or cont ==2 else search.materials_npi_ids
                    cont += 1
                    material_line = list(filter(lambda x:x!=False,list_materiales))
                    diseno_almacen = list(filter(lambda x:x.materials_list.id==self.materials_list.id,material_line))
                    cantidad_material = sum(list(map(lambda x:x.materials_availabe,diseno_almacen)))
                    suma += cantidad_material
                consulta.write({
                    "apartado": consulta.cantidad if suma > consulta.cantidad else suma,
                    "disponible":consulta.cantidad - suma if consulta.cantidad - suma > 0 else 0


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
    _name = "dtm.odt.sercicios"
    _description = "Modelo para la solicitud de servicios externos"

    extern_id = fields.Many2one("dtm.odt")

    nombre = fields.Char(string="Nombre del Servicio")
    cantidad = fields.Integer(string="Cantidad")
    tipo_orden = fields.Char(string="OT/NPI")
    numero_orden = fields.Integer(string="Orden")
    proveedor = fields.Char(string="Proveedor")
    fecha_solicitud = fields.Date(string="Fecha de Solicitud", default= datetime.today(),readonly=True)
    fecha_compra = fields.Date(string="Fecha de Compra",readonly=True)
    fecha_entrada = fields.Date(string="Fecha de Entrada",readonly=True)
    material_id = fields.One2many("dtm.odt.servmateriales","model_id")
    anexos_id = fields.Many2many("ir.attachment")

class MaterialeServicios (models.Model):
    _name = "dtm.odt.servmateriales"
    _description = "Modelo para la solicitud de materiales para servicios externos"

    model_id = fields.Many2one("dtm.odt.sercicios")

    # nombre = fields.Char(compute="_compute_material_list",store=True)
    nombre = fields.Char()
    medida = fields.Char()

    # materials_list = fields.Many2one("dtm.diseno.almacen", string="LISTADO DE MATERIALES",required=True)
    materials_cuantity = fields.Integer("CANTIDAD")
    materials_inventory = fields.Integer("INVENTARIO", readonly=True)
    materials_availabe = fields.Integer("APARTADO", readonly=True)
    # materials_required = fields.Integer("REQUERIDO",compute ="_compute_materials_inventory",store=True)
    materials_required = fields.Integer("REQUERIDO")

    # def consultaAlmacen(self,nombre,codigo):
    #      get_almacen =  self.env['dtm.materiales.otros'].search([("codigo", "=", codigo)])
    #      if get_almacen:
    #          return get_almacen
    #      if nombre:
    #          if re.match(".*[Ll][aáAÁ][mM][iI][nN][aA].*",nombre):
    #             get_almacen = self.env['dtm.materiales'].search([("codigo","=",codigo)])
    #          elif re.match(".*[aáAÁ][nN][gG][uU][lL][oO][sS]*.*",nombre):
    #             get_almacen = self.env['dtm.materiales.angulos'].search([("codigo","=",codigo)])
    #          elif re.match(".*[cC][aA][nN][aA][lL].*",nombre):
    #             get_almacen = self.env['dtm.materiales.canal'].search([("codigo","=",codigo)])
    #          elif re.match(".*[pP][eE][rR][fF][iI][lL].*",nombre):
    #             get_almacen = self.env['dtm.materiales.perfiles'].search([("codigo","=",codigo)])
    #          elif re.match(".*[pP][iI][nN][tT][uU][rR][aA].*",nombre):
    #             get_almacen = self.env['dtm.materiales.pintura'].search([("codigo","=",codigo)])
    #          elif re.match(".*[Rr][oO][dD][aA][mM][iI][eE][nN][tT][oO].*",nombre):
    #             get_almacen = self.env['dtm.materiales.rodamientos'].search([("codigo","=",codigo)])
    #          elif re.match(".*[tT][oO][rR][nN][iI][lL][lL][oO].*",nombre):
    #             get_almacen = self.env['dtm.materiales.tornillos'].search([("codigo","=",codigo)])
    #          elif re.match(".*[tT][uU][bB][oO].*",nombre):
    #             get_almacen = self.env['dtm.materiales.tubos'].search([("codigo","=",codigo)])
    #          elif re.match(".*[vV][aA][rR][iI][lL][lL][aA].*",nombre):
    #             get_almacen = self.env['dtm.materiales.varilla'].search([("codigo","=",codigo)])
    #          elif re.match(".*[sS][oO][lL][eE][rR][aA].*",nombre):
    #             get_almacen = self.env['dtm.materiales.solera'].search([("codigo","=",codigo)])
    #          if len(get_almacen) > 1:
    #             raise ValidationError("Codigo duplicado, favor de borrar desde Almacén.")
    #      return  get_almacen
    #
    # @api.depends("materials_cuantity")
    # def _compute_materials_inventory(self):
    #     for result in self:
    #         result.materials_required = 0
    #         consulta  = result.consultaAlmacen(result.nombre,result.materials_list.id)
    #         if consulta:
    #             get_almacen = self.env['dtm.servicios.materiales'].search([("materials_list","=",consulta.codigo)])# Busca el material en todas las ordenes para sumar el total de requerido
    #             cantidad_total = 0 # Guarda las cantidades de materiales solicitadas de todas las ordenes
    #             consulta_disp = 0 #Guarda las cantidades del material apartado cuando este es igual o mayor al del stock(aparta)
    #             for item in get_almacen:#obtiene las dos variables anteriores al recorrer la tabla materials.line enfocandose en este item
    #                 cantidad_total+= item.materials_cuantity
    #                 consulta_disp += item.materials_availabe
    #             disp = consulta.cantidad - cantidad_total #Resetea el valor de disponible de la tabla del material correspondiente en el modulo Almacén
    #             if disp < 0:#Revisa si el dato es menor a cero y de serlo lo restablece a cero
    #                 disp = 0
    #             consulta.write({ # Actualiza los valores en la categoria correspondiente del modulo almacén
    #                 "disponible": disp,
    #                 "apartado": cantidad_total
    #             })
    #             #Hace toda la lógica de calculo
    #             cantidad = result.materials_cuantity
    #             inventario = consulta.cantidad
    #             apartado = result.materials_availabe
    #             if consulta_disp >= 0 and consulta_disp < inventario:
    #                 requerido = 0
    #                 apartado = cantidad
    #             else:
    #                 requerido = cantidad - apartado
    #
    #             if cantidad <= apartado:
    #                 apartado = cantidad
    #             if apartado < 0:
    #                 apartado = 0
    #             if requerido < 0:
    #                 requerido = 0
    #             result.materials_inventory = inventario
    #             result.materials_availabe = apartado
    #             self.env['dtm.servicios.materiales'].search([("id","=",self._origin.id)]).write({"materials_availabe":apartado})
    #             result.materials_required = requerido
    #             cantidad_total = 0 # Guarda las cantidades de materiales solicitadas de todas las ordenes
    #             consulta_disp = 0 #Guarda las cantidades del material apartado cuando este es igual o mayor al del stock(aparta)
    #             for item in get_almacen:#obtiene las dos variables anteriores al recorrer la tabla materials.line enfocandose en este item
    #                 cantidad_total+= item.materials_cuantity
    #                 consulta_disp += item.materials_availabe
    #             disp = consulta.cantidad - cantidad_total #Resetea el valor de disponible de la tabla del material correspondiente en el modulo Almacén
    #             if disp < 0:#Revisa si el dato es menor a cero y de serlo lo restablece a cero
    #                 disp = 0
    #             consulta.write({ # Actualiza los valores en la categoria correspondiente del modulo almacén
    #                 "disponible": disp,
    #                 "apartado": cantidad_total
    #             })
    #
    # @api.depends("materials_list")
    # def _compute_material_list(self):
    #     for result in self:
    #         result.nombre = result.materials_list.nombre
    #         result.medida = result.materials_list.medida







