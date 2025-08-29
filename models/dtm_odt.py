from email.policy import default
from re import search

from odoo import api,models,fields
from datetime import datetime
from odoo.exceptions import ValidationError
from fractions import Fraction
import re
import pytz
import os

from pkg_resources import require


class DtmOdt(models.Model):
    _name = "dtm.odt"
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Oden de trabajo"
    _order = "ot_number desc"
    _rec_name = "ot_number"

    #---------------------Basicos----------------------
    def action_autoNum(self): # Genera número consecutivo de NPI
        get_terminado = self.env['dtm.facturado.npi'].search([],order='ot_number desc',limit=1)
        get_npi = self.env['dtm.odt'].search([("tipe_order","=","NPI")],order='ot_number desc', limit=1)
        return 0 if self.tipe_order in ['Pre'] else get_npi.ot_number + 1 if get_npi.ot_number > get_terminado.ot_number else get_terminado.ot_number + 1
    # Campo para llevar el conteo exclusivo de diseño
    od_number = fields.Integer(string="OD",readonly=True)
    ot_number = fields.Integer(string="OT",default=action_autoNum,readonly=True)
    tipe_order = fields.Char(string="TIPO",readonly=True, default='NPI')
    revision_ot = fields.Integer(string="VERSIÓN",default=1,readonly=True) # Esto es versión
    name_client = fields.Char(string="CLIENTE",default='Nombre del Cliente')
    product_name = fields.Char(string="NOMBRE DEL PRODUCTO",default='Nombre del Producto')
    date_in = fields.Date(string="ENTRADA", default= datetime.today(),readonly=True)
    po_number = fields.Char(string="PO/Cot",readonly=True)
    date_rel = fields.Date(string="ENTREGA", default= datetime.today())
    version_ot = fields.Integer(string="REVISIÓN",default=1,readonly=True)# Esto es revisión
    color = fields.Char(string="COLOR",default="N/A",tracking=True)
    cuantity = fields.Integer(string="CANTIDAD",tracking=True)
    materials_ids = fields.One2many("dtm.materials.line","model_id",string="Lista")
    lista_material_id = fields.One2many("dtm.odt.listamateriales","model_id")
    disenador = fields.Char("Diseñador")
    firma = fields.Char(string="Firma", readonly = True)
    firma_produccion = fields.Char()
    firma_almacen = fields.Char(string="Firma Almacén",readonly = True)
    almacen_rev = fields.Boolean()
    firma_ventas = fields.Char(string="Aprobado",readonly=True)
    firma_calidad = fields.Char(string='Revisado',readonly=True)
    firma_ingenieria = fields.Char(string="Nesteo", readonly = True)
    po_fecha_creacion = fields.Date(string="Creación PO", readonly=True)
    po_fecha = fields.Date(string="Fecha PO", readonly=True)
    planos = fields.Boolean(string="Planos",default=False)
    nesteos = fields.Boolean(string="Nesteos",default=False)

    rechazo_id = fields.One2many("dtm.odt.rechazo", "model_id")
    anexos_ventas_id = fields.Many2many("ir.attachment" ,"anexos_ventas_id",string="Archivos")
    anexos_id = fields.Many2many("ir.attachment" ,"anexos_id",string="Archivos")
    # Máquinas de corte laser
    cortadora_id = fields.Many2many("ir.attachment", "cortadora_id",string="Segundas piezas")
    primera_pieza_bfc_id = fields.Many2many("ir.attachment", "primera_pieza_bfc_id",string="Primeras piezas")
    bfc_id = fields.Many2many("ir.attachment", "bfc_id",string="Segundas piezas")
    primera_pieza_id = fields.Many2many("ir.attachment", "primera_pieza_id",string="Primeras piezas")
    #----------------------------
    tubos_id = fields.Many2many("ir.attachment", "tubos_id")
    no_cotizacion = fields.Char('')
    orden_compra_pdf = fields.Many2many("ir.attachment",string='File', readonly =True)
    ligas_id = fields.One2many("dtm.odt.ligas","model_id")
    ligas_tubos_id = fields.One2many("dtm.odt.ligas","model_tubo_id")
    archivos_id = fields.Many2many('dtm.documentos.anexos')
    date_disign_finish = fields.Datetime(string="Fecha Diseño",readonly =True)
    diseno_terminado = fields.Datetime(string="Diseño Terminado/hrs", readonly = True)
    diseno_duracion = fields.Float(string="Tiempo de diseño",compute= '_compute_duracion', readonly = True)
    manufactura = fields.Boolean(string="P",default=False)
    nesteo_chk = fields.Boolean(string="N",default=False)
    intervencion_calidad =  fields.Boolean(string='Revisión Calidad',default=False,readonly=True)
    nesteo_inicio = fields.Datetime()
    nesteo_final = fields.Datetime()
    tiempo_nesteo = fields.Float(string='Tiempo de Nesteo/hrs',readonly=True)
    # Prediseño
    prediseno_id = fields.Many2many('ir.attachment', 'prediseno_final_diseno', string="Prediseño")
    # liga_id = fields.Many2many('dtm.necesidades.prediseno.ligas', string="Ligas")

    #---------------------Resumen de descripción------------
    description = fields.Text(string="DESCRIPCIÓN",tracking=True)

    #------------------------Notas---------------------------
    notes = fields.Text(string="Notas",tracking=True)

    liberado = fields.Char()
    retrabajo = fields.Boolean(default=False) #Al estar en verdadero pone todos los campos en readonly
    bitacora_id = fields.One2many('dtm.odt.retrabajo','model_id')

    maquinados_id = fields.One2many("dtm.odt.servicios","extern_id")

    usuario = fields.Char(string="Usuario", compute = "_compute_usuario")
    costo_material = fields.Float(string="Costo",readonly = True)
    costo_diseno = fields.Float(string="Costo Diseno", compute = 'compute_costo_diseno')

    #----------------Tracking----------------------------
    lista_material_id_tracking = fields.Char(compute='_compute_lista_material_id_tracking', store=True, tracking = True)
    materials_ids_tracking = fields.Char(compute='_compute_materials_ids_tracking', store=True, tracking = True)
    maquinados_id_tracking = fields.Char(compute='_compute_maquinados_id_tracking', store=True, tracking = True)
    anexos_id_tracking = fields.Char(compute='_compute_anexos_id_tracking', store=True, tracking = True)

    @api.depends('anexos_id')
    def _compute_anexos_id_tracking(self):
        for record in self:
            record.maquinados_id_tracking = ", ".join(
                [f"ir.attachment:{item.ids}\n" for item in
                 record.anexos_id])

    @api.depends('maquinados_id')
    def _compute_maquinados_id_tracking(self):
        for record in self:
            record.maquinados_id_tracking = ", ".join([f"{item.nombre},{item.cantidad},ir.attachment:{item.anexos_id.ids}\n" for item in record.maquinados_id])


    @api.depends('lista_material_id')
    def _compute_lista_material_id_tracking(self):
        for record in self:
            record.lista_material_id_tracking = ", ".join([f"{item.material_id.id},{item.material_id.nombre}, {item.material_id.medida}, c:{item.cantidad}\n"for item in record.lista_material_id])

    @api.depends('materials_ids')
    def _compute_materials_ids_tracking(self):
        for record in self:
            record.materials_ids_tracking = ", ".join([f"{item.materials_list.id},{item.materials_list.nombre}, {item.materials_list.medida}, c:{item.materials_cuantity}, a:{item.materials_availabe}, r:{item.materials_required}, C:{item.revision}, A:{item.almacen}\n"for item in record.materials_ids])
    #-------------------------------------------------------
    def compute_costo_diseno(self):
        for result in self:
            result.costo_diseno = sum(result.lista_material_id.mapped('precio'))

    def compute_costo_material(self):
        for result in self:
            result.costo_material = sum(result.materials_ids.mapped('costo'))

    # Calcula el tiempo que duró el proceso de diseño
    def _compute_duracion(self):
        for result in self:
            # print(result.id,result.diseno_terminado)
            if result.diseno_terminado:
                result.diseno_duracion = round((result.diseno_terminado - result.create_date).total_seconds() / 3600.0, 2)
            else:
                result.diseno_duracion = 0

    def action_version(self):
        version = self.env['dtm.odt'].search([('ot_number','=',self.ot_number),('revision_ot','=',self.revision_ot + 1)])
        if not version:
            version.create({
                'od_number': self.od_number,
                'ot_number': self.ot_number,
                'tipe_order': self.tipe_order,
                'revision_ot': self.revision_ot + 1,
                'name_client': self.name_client,
                'product_name': self.product_name,
                'date_in': self.date_in,
                'po_number': self.po_number,
                'date_rel': self.date_rel,
                'version_ot': self.version_ot,
                'color': self.color,
                'cuantity': self.cuantity,
                'materials_ids': [(5, 0, {})],
                'disenador': 'Luis' if self.disenador == 'garcia' else 'Andrés',
                'firma': False,
                'firma_almacen': '',
                'almacen_rev': False,
                'firma_ventas': False,
                'firma_calidad': '',
                'firma_ingenieria': False,
                'po_fecha_creacion': self.po_fecha_creacion,
                'po_fecha': self.po_fecha,
                'planos': False,
                'nesteos': False,
                'rechazo_id':[(5, 0, {})],
                'anexos_ventas_id':self.anexos_ventas_id,
                'anexos_id':[(5, 0, {})],
                'cortadora_id':[(5, 0, {})],
                'primera_pieza_id':[(5, 0, {})],
                'tubos_id':[(5, 0, {})],
                'no_cotizacion':self.no_cotizacion,
                'orden_compra_pdf':self.orden_compra_pdf,
                'ligas_id':[(5, 0, {})],
                'ligas_tubos_id':[(5, 0, {})],
                'archivos_id':self.archivos_id,
                'date_disign_finish':self.date_disign_finish,
                'manufactura':False,
                'nesteo_chk':False,
                'intervencion_calidad':self.intervencion_calidad,
            })
        # print(version,self.ot_number,self.revision_ot)

    def action_orden_hijo(self):
        get_diseno_odt = self.env['dtm.odt'].search([('ot_number', '!=', False)], order='ot_number desc', limit=1)
        get_diseno_fact = self.env['dtm.facturado.odt'].search([('ot_number', '!=', False)],
                                                                       order='ot_number desc', limit=1)
        ot_number = max(get_diseno_odt.ot_number, get_diseno_fact.ot_number) + 1

        vals= {
                'description':self.description,
                'od_number': None,
                'ot_number': ot_number,
                'tipe_order': 'OT',
                'revision_ot': self.ot_number,
                'name_client': self.name_client,
                'product_name': self.product_name,
                'date_in': self.date_in,
                'po_number': self.po_number,
                'date_rel': self.date_rel,
                'version_ot': self.version_ot,
                'color': self.color,
                'cuantity': 0,
                'materials_ids': [(0, 0, {
                                                'nombre':material.nombre,
                                                'medida':material.medida,
                                                'notas':material.notas,
                                                'materials_list':material.materials_list.id,
                                                'materials_cuantity':material.materials_cuantity,
                                                'costo':material.costo,
                                            }) for material in self.materials_ids],
                'lista_material_id':[(0, 0, {
                                                'material_id':material.material_id.id,
                                                'cantidad':material.cantidad,
                                                'precio':material.precio,
                                            }) for material in self.lista_material_id],
                'disenador': self.disenador,
                'firma': self.firma,
                'firma_almacen': '',
                'almacen_rev': False,
                'firma_ventas': False,
                'firma_calidad': '',
                'firma_ingenieria': False,
                'po_fecha_creacion': self.po_fecha_creacion,
                'po_fecha': self.po_fecha,
                'planos': self.planos,
                'nesteos': False,
                'rechazo_id': [(5, 0, {})],
                'anexos_ventas_id': self.anexos_ventas_id,
                'anexos_id': [(5, 0, {})],
                'cortadora_id': [(5, 0, {})],
                'primera_pieza_id': [(5, 0, {})],
                'tubos_id': [(5, 0, {})],
                'no_cotizacion': self.no_cotizacion,
                'orden_compra_pdf': self.orden_compra_pdf,
                'ligas_id': [(5, 0, {})],
                'ligas_tubos_id': [(5, 0, {})],
                'archivos_id': self.archivos_id,
                'date_disign_finish': self.date_disign_finish,
                'manufactura': False,
                'nesteo_chk': False,
                'intervencion_calidad': self.intervencion_calidad,
            }
        # print(vals)
        self.env['dtm.odt'].create(vals)
        return {
            'name': 'Orden Creada',
            'type': 'ir.actions.act_window',
            'res_model': 'confirm.dialog.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_message': f'La Orden {ot_number} se ha creado correctamente.'
            }
        }

    def action_almacen(self):
        if any(not m.almacen for m in self.materials_ids):
            self.almacen_rev = True
            self.firma_almacen = 'Pendiente'
        else:
            self.firma_almacen = 'almacen@dtmindustry.com'

        if not self.materials_ids:
            self.firma_almacen = None

    def action_pasive(self):
        pass

    def _compute_usuario(self):
        for result in self:
            # print(self.env.user.partner_id.email)
            result.usuario = self.env.user.partner_id.email
    # ----------------------------------- Funciones ----------------------------------------------------------
    def firma_diseno(self,email,parcial):
        # Pone el nombre del diseñador
        self.firma = self.env.user.partner_id.name
        if self.tipe_order in ["OT","NPI"]:
            if not self.ot_number:
                get_this = self.env['dtm.odt'].search([],order="ot_number desc",limit=1) #Obtiene el último número de orden
                get_facturado = self.env['dtm.facturado.odt'].search([],order="ot_number desc",limit= 1) #Obtiene el último número de las ordenes facturado
                self.ot_number = max(get_this.ot_number,get_facturado.ot_number) + 1 #Obtiene el último número de orden
            get_ventas = self.env['dtm.compras.items'].search([("orden_diseno","=",self.od_number)])
            get_ventas.write({"firma": self.firma,"orden_trabajo":self.ot_number})#Pone el número de la orden de trabajo en ventas

    #Revisión de la lista de materiales antes de mandarse a compras
    def materiales_check(self):
        for row in self.materials_ids: # Se mandan comprar los items con cantidad mayor a cero y revisado por almacén
            #Se manda comprar el item si es mayor a cero y esta revisado por almacén
            row.write({'revision':True}) if row.almacen and row.materials_required > 0 else row.write({'revision':False})
            # Se verifica si es una lámina
            if row.materials_list.nombre.find("Lámina") != -1: #Se verifica que no sea pedacería
                medidas_validas = ["120.0 x 48.0", "96.0 x 48.0", "120.0 x 36.0", "96.0 x 36.0", "60.0 x 48.0"]
                if not any(medida in row.materials_list.medida for medida in medidas_validas):#Se pone falso si la lámina no se encuentra en las medidas de la lista
                    row.write({'revision':False})

    def prediseño_terminado(self):
        cotizacion = self.env['dtm.cotizaciones.predisenos'].search([('od_number','=',self.od_number),('product_name','=',self.product_name),('description','=',self.description)],limit=1)
        # print('Prediseño',cotizacion)
        if cotizacion:
            cotizacion.write({
                'prediseno_id':[(6,0,self.prediseno_id.ids)],
                'liga_id':[(6,0,self.liga_id.ids)]
            })
            self.unlink()

    # Metodo para controlar el paso a proceso
    def action_firma(self,parcial=False):
        self.materiales_check() # Pone verdadero la casilla de ventas si esta es mayor a cero y está revisado por almacén
        email = self.env.user.partner_id.email
        # self.disenador = self.firma  and not self.disenador else None
        if self.tipe_order == 'NPI' and not self.disenador and email in ['ingenieria@dtmindustry.com', 'ingenieria2@dtmindustry.com', 'ingenieria1@dtmindustry.com']:
            self.disenador = self.env.user.partner_id.name
        if self.intervencion_calidad: # Solo si se solicita la intervención de calidad
            if email in ['calidad@dtmindustry.com', 'calidad2@dtmindustry.com']:
                self.firma_calidad = self.env.user.partner_id.name
            elif email in ['hugo_chacon@dtmindustry.com', 'ventas1@dtmindustry.com'] and self.tipe_order != "SK" and self.tipe_order != "PD" and self.firma_calidad:
                self.firma_ventas = self.env.user.partner_id.name
                self.proceso(parcial)
            elif email in ['ingenieria@dtmindustry.com', 'ingenieria2@dtmindustry.com', 'ingenieria1@dtmindustry.com']:
                self.firma_diseno(email,parcial)
            else:
                raise ValidationError('Se requiere revisión de calidad')
        # Firma Diseñador, Ventas
        elif email in ['hugo_chacon@dtmindustry.com', 'ventas1@dtmindustry.com', 'rafaguzmang@hotmail.com'] and self.tipe_order not in ("SK", "PD") and not self.firma_ventas and self.firma:
            # Firma de aprobación de OT
                self.firma_ventas = self.env.user.partner_id.name
                self.maquinados()  # Manda los servicios a maquinados
                self.diseno_terminado = datetime.today()
                self.retrabajo = True
                self.proceso(parcial)


        # Firma Diseñador
        elif email in ['ingenieria@dtmindustry.com', 'ingenieria2@dtmindustry.com', 'ingenieria1@dtmindustry.com']:
            # Firma de diseño
            if not self.firma:
                self.firma_diseno(email, parcial)


            # Solo ingenieria1 puede liberar oficialmente
            if email == 'ingenieria1@dtmindustry.com' and self.firma_ventas and not self.firma_ingenieria:
                if not self.firma_ingenieria:
                    self.firma_ingenieria = self.env.user.partner_id.name

        # Ejecutar proceso automáticamente si todas las Firmas(3) están listas
        if self.firma in ['Luis Donaldo García Rayos','Andrés Alberto Orozco Martínez','Bryan Banda'] and self.firma_ventas in ['Alejandro Erives Chavez','Hugo Chacon','Administrator'] and self.tipe_order != 'COT':
            self.nesteo_chk = True
            if not self.nesteo_inicio:
                self.nesteo_inicio = fields.Datetime.now()

            if not self.materials_ids:
                self.materiales_nesteo()
        # Si la orden es un prediseño
            if self.tipe_order == 'Pre':
                self.prediseño_terminado()

        if self.firma and self.firma_ventas and self.firma_ingenieria and self.tipe_order not in ['COT','Pre'] :
            self.nesteo_chk = False
            self.manufactura = True
            self.maquinados()
            self.proceso(parcial)
            # print(self.nesteo_final ,self.cortadora_id ,self.primera_pieza_id , self.tubos_id)
            if not self.nesteo_final and (self.cortadora_id or self.primera_pieza_id or self.tubos_id):
                self.nesteo_final = fields.Datetime.now()
                # print(self.nesteo_final)
        if self.nesteo_final and self.nesteo_inicio :
            self.tiempo_nesteo = round((self.nesteo_final - self.nesteo_inicio ).total_seconds() / 3600.0,2)
            # print(self.tiempo_nesteo,self.nesteo_final,self.nesteo_inicio)
        self.action_almacen()

    def materiales_nesteo(self):
        lista = []

        if self.env['dtm.odt'].search([('ot_number','=',self.revision_ot)],limit=1):
            for item in self.lista_material_id:
                vals = {
                    'model_id': item.model_id.id,
                    'nombre': item.material_id.nombre,
                    'medida': item.material_id.medida,
                    'materials_list': item.material_id.id,
                    'materials_cuantity': 0,
                    'usuario': item.usuario,
                    'materials_availabe': 0,
                    'materials_required':0
                }
                to_materiales = self.materials_ids.search([('model_id','=',item.model_id.id),('materials_list','=',item.material_id.id)])
                to_materiales.write(vals) if to_materiales else to_materiales.create(vals)

        else:
            for item in self.lista_material_id:
                # Obtener stock
                stock = self.env['dtm.materiales'].browse(item.material_id.id)
                stock_total = stock.cantidad  # Campo float

                # Obtener total apartado (ordenado pero aún no entregado)
                apartado = sum(
                    self.env['dtm.materials.line']
                    .search([
                        ('materials_list', '=', item.material_id.id),
                        ('entregado', '!=', True),
                        ('revision', '!=', True),
                        ('materials_cuantity', '>', 0)
                    ])
                    .mapped('materials_availabe')
                )

                # Calcular disponible
                disponible = stock_total - apartado

                # Inicializar
                requerido = 0
                nuevo_apartado = 0

                if disponible >= item.cantidad:
                    nuevo_apartado = item.cantidad
                    requerido = 0
                elif 0 < disponible < item.cantidad:
                    nuevo_apartado = disponible
                    requerido = item.cantidad - disponible
                else:
                    nuevo_apartado = 0
                    requerido = item.cantidad

                vals = {
                    'model_id':item.model_id.id,
                    'nombre':item.material_id.nombre,
                    'medida':item.material_id.medida,
                    'materials_list':item.material_id.id,
                    'materials_cuantity':item.cantidad,
                    'usuario':item.usuario,
                    'materials_availabe':max(0,nuevo_apartado),
                    'materials_required':max(0,requerido)
                }


                to_materiales = self.materials_ids.search([('model_id','=',item.model_id.id),('materials_list','=',item.material_id.id)])
                to_materiales.write(vals) if to_materiales else  to_materiales.create(vals)

    def proceso(self,parcial=False):
        get_ot = self.env['dtm.proceso'].search([("ot_number","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipe_order","=",self.tipe_order)])#Busca en procesos la orden
        get_ot.write({ #Pone firma de ventas en la orden en el modulo de procesos
            "firma_ventas": self.firma_ventas,
            "firma_ventas_kanba":"Ventas"
        })
        vals = { #Valores a crear o cambiar
                "ot_number":self.ot_number,
                "revision_ot":self.revision_ot,
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
                "color":self.color,
                "nesteos":True if self.cortadora_id or self.primera_pieza_id else False,
                "planos": True if self.anexos_id else False,
                "firma_diseno":self.firma
        }
        vals["firma_parcial"] = parcial
        if get_ot:#Actualiza la orden en procesos
            if (self.cortadora_id or self.primera_pieza_id) and get_ot.status == "aprobacion" :
                status = "corte"
            vals["status"] = get_ot.status
            get_ot.write(vals)
        else:
            status = "aprobacion" #Se pone el status en aprobación o en nesteos si hay archivos en las máquinas cortadoras
            if self.cortadora_id or self.primera_pieza_id:
                status = "corte"
            vals["status"] = status
            get_ot.create(vals)#Crea la orden en procesos
            get_ot = self.env['dtm.proceso'].search([("ot_number","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipe_order","=",self.tipe_order)])#Carga la orden de procesos

        get_ot.materials_ids = self.materials_ids #Carga la lista de materiales de la orden de diseño (dtm.odt) en la orden de trabajo (dtm.proceso)
        get_ot.write({'anexos_id': [(5, 0, {})]}) #Limpia los anexos para cargar los nuevos (Actualizar)
        lines = []
        for anexo in self.anexos_id:#Busca los archivos anexos en el ir.attachment
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
        list_archivos = []
        if self.primera_pieza_id or self.primera_pieza_bfc_id: #Busca los archivos de corte cuando hay primera pieza
            mitsubishi_archivos = self.cortadora_id  # Pasa los archivos de la segunda pieza
            bfc6032_archivos = self.bfc_id
            for archivos in [mitsubishi_archivos, bfc6032_archivos]:
                for archivo in archivos:
                    list_archivos.append(archivo)
            for anexo in list_archivos:
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

        # Cortadora laser al modulo proceso
        # Cortadora de tubos al modulo proceso
        get_ot.write({'tubos_id': [(5, 0, {})]})
        lines = []
        for anexo in self.tubos_id: #Carga los archivos para corte de tubos en procesos
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
                vals['cortado'] = False
                get_anexos.create(vals)
                get_anexos = self.env['dtm.proceso.tubos'].search([("nombre","=",attachment.name),("documentos","=",attachment.datas)],order='nombre desc',limit=1)
                lines.append(get_anexos.id)
        get_ot.write({'tubos_id': [(6, 0, lines)]})

        self.compras_odt(self.materials_ids) # Se manda el material a compras
        #Revisa si la firma es de nesteo para mandar las ordenes a corte
        if self.env.user.partner_id.email in ['ingenieria1@dtmindustry.com','rafaguzmang@hotmail.com']:
            if self.firma_ingenieria:
                self.cortadora_laser()#Se manda cortar lámina
                self.cortadora_tubos()#Se manda cortar Perfilería

    def cortadora_laser(self):
        # print("cortadora_laser",self.cortadora_id,self.primera_pieza_id)
        if self.cortadora_id or self.primera_pieza_id or self.bfc_id or self.primera_pieza_bfc_id:
            # Se obtienen los datos de la orden del modulo de procesos
            get_proceso = self.env['dtm.proceso'].search([('ot_number','=',self.ot_number),('revision_ot','=',self.revision_ot),('tipe_order','=',self.tipe_order)])
            get_proceso.status == "aprobacion" and get_proceso.write({'status':"corte"})
            status = get_proceso.mapped('status')
            vals = {
                "orden_trabajo":self.ot_number,
                "revision_ot":self.revision_ot,
                "nombre_orden":self.product_name,
                "tipo_orden": self.tipe_order,
            }
            material_corte = ""
            # Se encargan de buscar la información necesaria -------------------------------
            get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipo_orden","=",self.tipe_order)])# Guarda la información (archivos) para pasar a corte
            # Proceso de corte
            get_encorte_primera = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipo_orden","=",self.tipe_order),("primera_pieza","=",True)])# Busca si la primera pieza está en proceso de corte
            get_encorte_segunda =  self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipo_orden","=",self.tipe_order),("primera_pieza","=",False)])# Busca si la segunda está en proceso de corte
            # Proceso de terminado
            get_cortado_primera = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipo_orden","=",self.tipe_order),("primera_pieza","=",True)]) # Busca si la primera pieza esta cortada
            get_cortado_segunda = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipo_orden","=",self.tipe_order),("primera_pieza","=",False)]) # Busca si las segundas piezas ya fueron cortadas
            # print(get_encorte_primera,get_encorte_segunda,get_cortado_primera,get_cortado_segunda)
            #---------------------------------------------------
            # Condicionales
            #    No exite este archivo en ningún modelo de la cortadora, de ser así procede a crearlo
            list_archivos = [] #lista para almacenar los archivos de corte
            # si no hay archivos
            if not get_encorte_primera and not get_encorte_segunda and not get_cortado_primera and not get_cortado_segunda:
                if self.primera_pieza_id or self.primera_pieza_bfc_id:
                    vals["primera_pieza"]= True
                    get_corte.create(vals) #Crea la orden de primera pieza
                    get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipo_orden","=",self.tipe_order),("primera_pieza","=",True)])# Carga la orden recien creada para su manipulación
                    mitsubishi_archivos = self.primera_pieza_id #Pasa los archivos de la primera pieza
                    bfc6032_archivos = self.primera_pieza_bfc_id
                else:
                    vals["primera_pieza"]= False
                    get_corte.create(vals) #Crea la orden de segunda pieza
                    get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipo_orden","=",self.tipe_order),("primera_pieza","=",False)])# Carga la orden recien creada para su manipulación
                    mitsubishi_archivos = self.cortadora_id # Pasa los archivos de la segunda pieza
                    bfc6032_archivos = self.bfc_id
                for archivos in [mitsubishi_archivos,bfc6032_archivos]:
                    for archivo in archivos:
                        list_archivos.append(archivo)
            # si el archivo es primera pieza y no ha sido cortado
            # elif get_encorte_primera and not get_corte_primer and not get_encorte_segunda and not get_corte_segunda:
            elif get_encorte_primera and not get_cortado_primera and not get_encorte_segunda and not get_cortado_segunda:
                # print("Primera pieza solo en corte")
                get_corte = get_encorte_primera
                get_corte.write(vals)
                # recolecta los archivos de las dos cortadoras
                mitsubishi_archivos = self.primera_pieza_id
                bfc6032_archivos = self.primera_pieza_bfc_id
                for archivos in [mitsubishi_archivos, bfc6032_archivos]:
                    for archivo in archivos:
                        list_archivos.append(archivo)
            # si hay segunda pieza
            elif not get_encorte_primera and get_cortado_primera and not get_encorte_segunda and not get_cortado_segunda:
                # print("Primera pieza cortada pero no hay segundas piezas")
                if self.primera_pieza_id or self.primera_pieza_bfc_id:
                    vals["primera_pieza"]= True
                    get_corte.create(vals) #Crea la orden de primera pieza
                    mitsubishi_archivos = self.primera_pieza_id
                    bfc6032_archivos = self.primera_pieza_bfc_id
                    get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipo_orden","=",self.tipe_order),("primera_pieza","=",True)])# Carga la orden recien creada para su manipulación
                    get_terminado = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipo_orden","=",self.tipe_order),("primera_pieza","=",True)])
                    for archivos in [mitsubishi_archivos, bfc6032_archivos]:
                        for archivo in archivos:
                            list_archivos.append(archivo)
                    if get_terminado:# Si hay archivos cortados los quita del retrabajo
                        archivos_cortados = get_terminado.cortadora_id.ids
                        record_ids = [] #Almacena los id que serán agregados para ser cortados
                        record_nombres = [] #Lista para llenar con todos los archivos de los documentos cortados
                        for ordenes in get_terminado:#Proceso de busqueda en el modelo de archivos cortados (dtm_laser_realizados)
                            for orden in ordenes:
                                mapa = orden.cortadora_id.mapped("nombre")
                                record_nombres.extend(mapa)
                        for thisFile in list_archivos: #Compara los nuevos archivos con los ya cortados
                            attachment = self.env['ir.attachment'].browse(thisFile.id)
                            if attachment.name in record_nombres:
                                record_nombres.remove(attachment.name)
                            else:
                                record_nombres.append(attachment.name)
                                record_ids.append(attachment.id)
                        recordset = self.env['ir.attachment'].browse(record_ids)
                        list_archivos = recordset #Pasa los archivos de la segunda pieza
            elif get_encorte_segunda:#Revisa que la primera pieza sea liberada que primera pieza esté cortada
                # Segunda pieza en corte
                # print("Segunda pieza en corte")
                vals["primera_pieza"]= False
                get_corte = get_encorte_segunda
                get_corte.write(vals)
                bfc6032_archivos = self.bfc_id
                mitsubishi_archivos = self.cortadora_id
                for archivos in [mitsubishi_archivos, bfc6032_archivos]:
                    for archivo in archivos:
                        list_archivos.append(archivo)
                get_terminado = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipo_orden","=",self.tipe_order),("primera_pieza","=",False)])
                if get_terminado:# Si hay archivos cortados los quita del retrabajo
                    record_ids = [] #Almacena los id que serán agregados para ser cortados
                    record_nombres = [] #Lista para llenar con todos los archivos de los documentos cortados
                    for ordenes in get_terminado:#Proceso de busqueda en el modelo de archivos cortados (dtm_laser_realizados)
                        for orden in ordenes:
                            mapa = orden.cortadora_id.mapped("nombre")
                            record_nombres.extend(mapa)
                    for thisFile in list_archivos: #Comprara los nuevos archivos con los ya cortados
                        attachment = self.env['ir.attachment'].browse(thisFile.id)
                        if attachment.name in record_nombres:
                            record_nombres.remove(attachment.name)
                        else:
                            record_nombres.append(attachment.name)
                            record_ids.append(attachment.id)
                    recordset = self.env['ir.attachment'].browse(record_ids)
                    list_archivos = recordset #Pasa los archivos de la segunda pieza
            elif not get_encorte_segunda and get_cortado_segunda:
                # print("Segunda pieza")
                vals["primera_pieza"]= False
                get_corte.create(vals) #Crea la orden de segunda pieza
                get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipo_orden","=",self.tipe_order),("primera_pieza","=",False)])# Carga la orden recien creada para su manipulación
                # Pasa los archivos de la segunda pieza
                bfc6032_archivos = self.bfc_id
                mitsubishi_archivos = self.cortadora_id
                for archivos in [mitsubishi_archivos, bfc6032_archivos]:
                    for archivo in archivos:
                        list_archivos.append(archivo)
                get_terminado = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipo_orden","=",self.tipe_order),("primera_pieza","=",False)])
                if get_terminado:# Si hay archivos cortados los quita del retrabajo
                    record_ids = [] #Almacena los id que serán agregados para ser cortados
                    record_nombres = [] #Lista para llenar con todos los archivos de los documentos cortados
                    for ordenes in get_terminado:#Proceso de busqueda en el modelo de archivos cortados (dtm_laser_realizados)
                        for orden in ordenes:
                            mapa = orden.cortadora_id.mapped("nombre")
                            record_nombres.extend(mapa)
                    for thisFile in list_archivos: #Comprara los nuevos archivos con los ya cortados
                        attachment = self.env['ir.attachment'].browse(thisFile.id)
                        if attachment.name in record_nombres:
                            record_nombres.remove(attachment.name)
                        else:
                            record_nombres.append(attachment.name)
                            record_ids.append(attachment.id)
                    recordset = self.env['ir.attachment'].browse(record_ids)
                    list_archivos = recordset #Pasa los archivos de la segunda pieza
            #-----------------------------------------------------------------------------------------------------------------------


            lines = []
            get_corte.write({'cortadora_id': [(5, 0, {})]})#limpia la tabla de los archivos
            for file in list_archivos:
                attachment = self.env['ir.attachment'].browse(file.id)
                vals = {
                    "documentos":attachment.datas,
                    "nombre":attachment.name,
                    "orden_trabajo":self.ot_number,
                    "revision_ot":self.revision_ot,
                    "primera_pieza":False,
                    "cortadora":'Mitsubishi' if file.id in self.primera_pieza_id.ids or file.id in self.bfc_id.ids else 'BFC6025',
                    "model_id": get_corte.id
                }
                # if not self.liberado:
                if self.primera_pieza_id and not self.liberado:
                    vals["primera_pieza"] = True
                get_files = self.env['dtm.documentos.cortadora'].search([("nombre","=",file.name),("orden_trabajo","=",self.ot_number),("revision_ot","=",self.revision_ot)],order='nombre desc',limit=1)
                if get_files:
                    get_files.write(vals)
                    lines.append(get_files.id)
                else:
                    vals['cortado'] = False
                    vals['contador'] = 0
                    get_files.create(vals)
                    get_files = self.env['dtm.documentos.cortadora'].search([("nombre","=",file.name)],order='nombre desc',limit=1)
                    lines.append(get_files.id)
            get_corte.write({'cortadora_id': [(6, 0, lines)]})

            # Busca todo el material que sea lámina
            lines = []  # Lista para agregar lo ids que serán encontrados
            get_corte.write({"materiales_id":[(5, 0, {})]})#Pasa los materiales correspondientes de la orden
            for lamina in self.materials_ids:
                if re.match("Lámina",lamina.nombre): # Revisa si el material tiene la palabra lámina de no ser así lo descarta
                    get_almacen = self.env['dtm.materiales'].search([("id","=",lamina.materials_list.id)]) # Busca el material en el almacén por codigo
                    localizacion = ""
                    # if get_almacen.localizacion:  # Si tiene localización la asigna
                    #     localizacion = get_almacen.localizacion
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
            # Busca los materiales en el modelo dtm.cortes.realizado para quitarlos de lines
            get_lamina_cortadas = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipo_orden","=",self.tipe_order)])#Busca si hay materiales cortados
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

    def cortadora_tubos(self):
        if self.tubos_id: #Agrega los datos a la máquina de corte
            vals = {
                "orden_trabajo":self.ot_number,
                "fecha_entrada": datetime.today(),
                "nombre_orden":self.product_name,
                "tipo_orden": self.tipe_order,
                "revision_ot":self.revision_ot
            }
            get_corte = self.env['dtm.tubos.corte'].search([("orden_trabajo","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipo_orden","=",self.tipe_order)])
            get_corte.write(vals) if get_corte else get_corte.create(vals)
            get_corte = self.env['dtm.tubos.corte'].search([("orden_trabajo","=",self.ot_number),('revision_ot','=',self.revision_ot),("tipo_orden","=",self.tipe_order)])

            # Se obtinen los archivos de corte para mandar a la cortadora de tubos
            lines = []
            for file in self.tubos_id:
                # Busca el documento en ir.attachment para obtener los datos necesarios
                attachment = self.env['ir.attachment'].browse(file.id)
                vals = {
                    "documentos":attachment.datas,
                    "nombre":attachment.name,
                    "model_id":get_corte.id
                }
                # Busca el documento en dtm.tubos.documentos para agregarlo en caso de que no este o en caso contrario actualizarlo
                get_files = self.env['dtm.tubos.documentos'].search([("nombre","=",file.name),("documentos","=",attachment.datas),("model_id","=",get_corte.id)], order='id desc',limit=1)
                get_cortado = self.env['dtm.tubos.realizados'].search(
                    [('orden_trabajo', '=', self.ot_number), ('revision_ot', '=', self.revision_ot),
                     ('tipo_orden', '=', self.tipe_order)], limit=1).cortadora_id.mapped('nombre')
                # print(get_cortado)
                if not attachment.name in get_cortado:
                    get_files.create(vals)
                else:
                    get_files.write(vals)

            lines = []
            # Se obtiene la lista de materiales para agregar a la cortadora de tubos (Perfiles)
            if self.materials_ids:
                  for material in self.materials_ids:
                    # Se revisa si es un tipo de Perfil
                    for match in ['Canales','Cuadrado','I.P.R.','P.T.R.','Redondo','Rectangular','Perfil','Tubo','Varilla']:
                        if material.materials_list.nombre.find(match) != -1:
                            # Se obtienen los datos del material para mandarlo al modulo dtm.tubos.corte
                            content = {
                                "identificador": material.materials_list.id,
                                "nombre": material.materials_list.nombre,
                                "medida": material.materials_list.medida,
                                "cantidad": material.materials_cuantity,
                                "inventario": material.materials_inventory,
                                "requerido": material.materials_required,
                            }
                            get_cortadora_laminas = self.env['dtm.tubos.materiales'].search([
                                ("identificador","=",material.materials_list.id),
                                ("nombre","=",material.materials_list.nombre),
                                ("medida","=",material.materials_list.medida),
                                ("cantidad","=",material.materials_cuantity),
                                ("inventario","=",material.materials_inventory),
                                ("requerido","=",material.materials_required)])
                            if get_cortadora_laminas:
                                get_cortadora_laminas.write(content)
                                lines.append(get_cortadora_laminas.id)
                            else:
                                get_cortadora_laminas.create(content)
                                get_cortadora_laminas = self.env['dtm.tubos.materiales'].search([
                                    ("identificador", "=", material.materials_list.id),
                                    ("nombre", "=", material.materials_list.nombre),
                                    ("medida", "=", material.materials_list.medida),
                                    ("cantidad", "=", material.materials_cuantity),
                                    ("inventario", "=", material.materials_inventory),
                                    ("requerido", "=", material.materials_required)])
                                lines.append(get_cortadora_laminas.id)
                  # Agrega la lista de materiales en la tabla materiales_id
                  get_corte.write({"materiales_id":[(6, 0,lines)]})

    def compras_odt(self,materiales):
        # ref == 2 and print(materiales,ref)
        # print(materiales.mapped('materials_list.id'))
        for codigo in materiales:
            # Si el item no tiene marcado el check box hace los calculos para el área de compras
            buscar = codigo.nombre # Se quita la leyenda Maquinado Externo
            buscar = buscar.replace("Maquinado Externo", "")
            # print(buscar,codigo.nombre)
            if codigo.revision and buscar.find('Maquinado') == -1:
                # Suma la cantidad requerida con los codigos repetidos dentro de la misma Orden
                cantidad_item = sum(self.env['dtm.materials.line'].search([("model_id","=",self.env['dtm.odt'].search([("ot_number","=",str(self.ot_number)),('revision_ot','=',self.revision_ot),("tipe_order","!=",'PD')]).id),("materials_list","=",codigo.materials_list.id)]).mapped('materials_required'))
                # cantidad_total = sum(self.env['dtm.materials.line'].search([("model_id","=",self.env['dtm.odt'].search([("ot_number","=",str(self.ot_number))]).id),("materials_list","=",codigo.materials_list.id)]).mapped('materials_'))

                # ref == 2 and print("Solicitado",cantidad_item)
                # Busca los materiales solicitados en el apartado de requerido
                get_compras = self.env['dtm.compras.requerido'].search([("orden_trabajo","ilike",str(self.ot_number)),('revision_ot','=',self.revision_ot),("codigo","=",codigo.materials_list.id)], limit=1)
                get_compras_odt = get_compras.mapped('orden_trabajo')
                get_compras_cantidad = get_compras.mapped('cantidad')
                # ref == 2 and print("Codigo",codigo.materials_list.id)
                list_reque_odt = list(set(",".join(get_compras_odt).replace(","," ").split()))
                list_reque_odt = list(filter(lambda x: x!=str(self.ot_number),list_reque_odt))
                total_reque = sum([self.env['dtm.materials.line'].search([("model_id","=",self.env['dtm.odt'].search([("ot_number","=",item),("tipe_order","!=",'PD')]).id),("materials_list","=",codigo.materials_list.id)]).materials_required for item in list_reque_odt])

                cantidad_reque = sum(get_compras_cantidad) - total_reque
                # ref == 2 and print("Requerido",cantidad_reque)

                # Busca los materiales solicitados en el apartado de comprado
                get_comprado = self.env['dtm.compras.realizado'].search([("orden_trabajo","ilike",str(self.ot_number)),('revision_ot','=',self.revision_ot),("codigo","=",codigo.materials_list.id),("comprado","=",False)])
                get_comprado_odt = get_comprado.mapped('orden_trabajo')
                get_comprado_cantidad = get_comprado.mapped('cantidad')
                # ref == 2 and print(get_comprado,get_comprado_odt,get_comprado_cantidad)
                list_comprado_odt = list(set(",".join(get_comprado_odt).replace(","," ").split()))
                # ref == 2 and print(list_comprado_odt)
                list_comprado_odt = list(filter(lambda x: x!=str(self.ot_number),list_comprado_odt))
                # ref == 2 and print(list_comprado_odt)
                total_comprado = sum([self.env['dtm.materials.line'].search([("model_id","=",self.env['dtm.odt'].search([("ot_number","=",item)]).id),("materials_list","=",codigo.materials_list.id)]).materials_required for item in list_comprado_odt])

                # ref == 2 and print("--",sum(get_comprado_cantidad),total_comprado)
                cantidad_comprado = (sum(get_comprado_cantidad) if sum(get_comprado_cantidad) > 0 else 0) - (total_comprado if total_comprado > 0 else 0)
                # ref == 2 and print("Comprado",cantidad_comprado)
                # ref == 2 and print("Comparación",cantidad_item,cantidad_comprado)
                # ref == 2 and print("------------------------------------------------------------------------------------------------------------------------------------------------------")
                # print(get_compras.disenador)
                # print(self.firma if not get_compras.disenador else "")
                medida = self.env['dtm.materiales'].search([('id','=',codigo.materials_list.id)]).medida
                vals = {
                        'orden_trabajo':self.ot_number,
                        'codigo':codigo.materials_list.id,
                        'nombre':f"{self.env['dtm.materiales'].search([('id','=',codigo.materials_list.id)]).nombre} {medida if medida else ''}",
                        'cantidad':cantidad_item - cantidad_comprado,
                        'disenador':self.disenador,
                        'tipo_orden':self.tipe_order,
                        'revision_ot':self.revision_ot,
                        'nesteo': True if self.firma_ingenieria else False
                    }
                # print(vals)
                # if get_compras.disenador:
                #     vals['disenador'] = get_compras.disenador
                get_compras = self.env['dtm.compras.requerido'].search([("orden_trabajo","=",str(self.ot_number)),('revision_ot','=',self.revision_ot),("codigo","=",codigo.materials_list.id)])
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


    def maquinados(self):
        # se verifica si los servicios existen en el modulo de maquinados
        if 'maquinado' in self.maquinados_id.mapped('tipo_servicio'):
            maquinado = self.env['dtm.maquinados'].search([('orden_trabajo','=',self.ot_number),('revision_ot','=',self.revision_ot),('tipo_orden','=',self.tipe_order)],limit=1)
            vals = {
                'orden_trabajo':self.ot_number,
                'revision_ot':self.revision_ot,
                'tipo_orden':self.tipe_order,
                'disenador':self.disenador,
            }
             # si existe se actualiza la información si no se crea
            maquinado.write(vals) if maquinado else maquinado.create(vals)
            maquinado = self.env['dtm.maquinados'].search([('orden_trabajo', '=', self.ot_number), ('revision_ot', '=', self.revision_ot),('tipo_orden', '=', self.tipe_order)], limit=1)
            # se pasan todos los servicios de la orden a la tabla de la orden que esta en el modulo de maquinados
            # se recorren los servicios
            for servicio in self.maquinados_id:
                if servicio.tipo_servicio == 'maquinado':
                    vals_servicios = {
                        'nombre':servicio.nombre,
                        'tipo_servicio':'Maquinado',
                        'cantidad':servicio.cantidad,
                        'fecha_solicitud':servicio.fecha_solicitud,
                        'model_id':maquinado.id,
                        'anexos_id':servicio.anexos_id
                    }
                    servicio = self.env['dtm.maquinados.servicios'].search([('nombre','=',servicio.nombre),('tipo_servicio','=','Maquinado')])
                    servicio.write(vals_servicios) if servicio else servicio.create(vals_servicios)

    def action_retrabajo(self):

        if self.bitacora_id:
            self.retrabajo = False
            self.firma_ingenieria = None
            self.firma = None
        else:
            raise ValidationError("Bitácora de retrabajo vacía")


# ----------------------------------------------------- Jala los servicios ----------------------------------------------------------------------------
    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._sync_maquinados_to_materiales()
        return record

    def write(self, vals):
        res = super().write(vals)
        self._sync_maquinados_to_materiales()
        return res

    def _sync_maquinados_to_materiales(self):
        """Sincroniza maquinados con la lista de materiales."""

        # 🔧 siempre reposiciona la secuencia al último ID disponible
        self.env.cr.execute("""
                SELECT setval(
                    'dtm_materiales_id_seq',
                    COALESCE((SELECT MAX(id) FROM dtm_materiales), 1),
                    true
                );
            """)

        for rec in self:
            for servicio in rec.maquinados_id:
                # Busca el material correspondiente
                servicio_search = self.env['dtm.materiales'].search([
                    ('nombre', '=', f"Maquinado {servicio.nombre}")
                ], limit=1)
                # Si no existe, lo crea
                if not servicio_search:
                    servicio_search = self.env['dtm.materiales'].create({
                        'nombre': f"Maquinado {servicio.nombre}",
                        'medida': '.'
                    })
                # Relaciona con la lista de materiales
                list_material = self.env['dtm.odt.listamateriales'].search([
                    ('material_id', '=', servicio_search.id),
                    ('model_id', '=', rec.id)
                ], limit=1)

                vals = {
                    'model_id': rec.id,
                    'material_id': servicio_search.id,
                    'cantidad': servicio.cantidad
                }

                if list_material:
                    list_material.write(vals)
                else:
                    self.env['dtm.odt.listamateriales'].create(vals)



        # borra el servicio si este se quitó del modelo de servicios
        # ids_maquinados = self.maquinados_id.mapped('id')
        # materiales_a_eliminar = self.lista_material_id.filtered(lambda l:l.id not in ids_maquinados)
        # unlink_commands = [(3,material.id) for material in materiales_a_eliminar]
        # self.update({
        #     'lista_material_id':unlink_commands
        # })

    # --------------------------------- Botones del header ----------------------------------------------

    def action_imprimir_formato(self): # Imprime según el formato que se esté llenando
        return self.env.ref("dtm_odt.formato_orden_de_trabajo").report_action(self)

    def action_imprimir_materiales(self): # Imprime según el formato que se esté llenando
        return self.env.ref("dtm_odt.formato_lista_materiales").report_action(self)

#--------------------------------------- Get View -----------------------------------------------------

    def get_view(self, view_id=None, view_type='form', **options):
        res = super(DtmOdt,self).get_view(view_id, view_type,**options)

        get_this = self.env['dtm.odt'].search([])
        for odt in get_this:
            if self.env['dtm.proceso'].search([('ot_number','=',odt.ot_number),('revision_ot','=',odt.revision_ot)]):
                odt.manufactura = True

        # Pone precio a los materiales
        for item in self.env['dtm.materials.line'].search([]):
            # print(self.env['dtm.compras.requerido'].search([('codigo','=',item.materials_list.id),('orden_trabajo','=',str(self.env['dtm.odt'].search([('id','=',item.model_id.id)]).ot_number))]).unitario)
            # print(item.model_id.id)
            if self.env['dtm.compras.precios'].search([('codigo','=',item.materials_list.id)]):
                item.write({'costo':item.materials_cuantity * self.env['dtm.compras.precios'].search([('codigo','=',item.materials_list.id)]).precio})


        # get_materiales = self.env['dtm.odt.listamateriales'].search([('precio','=',0)]).mapped('material_id').ids
        # get_compras = self.env['dtm.compras.precios'].search([('codigo','in',get_materiales)]).mapped('codigo')
        # for item in get_compras:
        #     if item in get_materiales:
        #         get_self = self.env['dtm.odt.listamateriales'].search([('material_id','=',item)])
        #         get_precio = self.env['dtm.compras.precios'].search([('codigo','=',item)])
        #         if get_self:
        #             for material in get_self:
        #                 material.write({'unitario':get_precio.precio,'precio': material.cantidad * get_precio.precio})





        # Busca las ordenes que ya fueron facturadas y borra los materiales solicitados por esta de la tabla dtm_materials_line

        return res


    #-----------------------Materiales----------------------

class TestModelLine(models.Model):
    _name = "dtm.materials.line"
    _description = "Tabla de materiales"

    model_id = fields.Many2one("dtm.odt")
    nombre = fields.Char(compute="_compute_material_list",store=True,related='materials_list.nombre')
    medida = fields.Char(store=True, related='materials_list.medida')
    notas = fields.Char(string="Notas")

    materials_list = fields.Many2one("dtm.materiales", string="LISTADO DE MATERIALES",required=True)
    materials_cuantity = fields.Integer("CANTIDAD", required=True)
    materials_inventory = fields.Integer("INVENTARIO", readonly=True)
    materials_availabe = fields.Integer("INVENTARIO", readonly=True)
    materials_required = fields.Integer("REQUERIDO", readonly=True ,store=True, compute='_compute_materials_inventory')
    revision = fields.Boolean(string="COMPRAR",readonly=True)
    entregado = fields.Boolean(default=False)
    cant_entregada = fields.Integer()
    recibe = fields.Char()
    almacen = fields.Boolean(string="ALMACÉN",default=False,readonly=True)
    costo = fields.Float(string="Precio",readonly=True)
    usuario = fields.Char(string="Usuario", compute="_compute_usuario")

    @api.onchange('materials_cuantity')
    def _onchenge_materials_cuantity(self):
        if self.materials_list and self.materials_list.nombre.startswith("Lámina") and self.materials_list.medida.split('@')[0].strip() not in ["120.0 x 48.0", "96.0 x 48.0", "96.0 x 36.0", "60.0 x 48.0"] and self.materials_required > 0:
            raise ValidationError("Material agotado")




    @api.constrains('materials_cuantity')
    def _check_cantidad(self):
        for record in self:
            if record.materials_cuantity == 0:
                raise ValidationError(
                    "La cantidad en el código '%s' no puede ser cero. Por favor, ingrese un valor mayor a cero." % record.materials_list.id)

    def _compute_usuario(self):
        for result in self:
            result.usuario = self.env.user.partner_id.email

    @api.onchange("revision")
    def onchange_revision(self):
        if self.revision:
            if self.env['dtm.odt'].search([('id','=',self.model_id._origin.id)]).firma_almacen in ['almacen@dtmindustry.com']:
                if self.nombre.find("Lámina") != -1:
                    medidas_validas = ["120.0 x 48.0", "96.0 x 48.0", "120.0 x 36.0", "96.0 x 36.0"]
                    self.revision = True
                    if not any(medida in self.medida for medida in medidas_validas):
                        self.revision = False
                        raise ValidationError("Solo Láminas completas!!")
            else:
                raise ValidationError("Lista de materiales no verificada")

    @api.depends('materials_cuantity', 'materials_list', 'model_id.revision_ot')
    def _compute_materials_inventory(self):
        for line in self:
            material = line.materials_list
            if not material:
                line.update({
                    'materials_inventory': 0,
                    'materials_availabe': 0,
                    'materials_required': 0,
                })
                continue

            # --- CÁLCULO DE INVENTARIO (Solo Lectura) ---
            stock = material.cantidad

            # DOMINIO CORREGIDO: Maneja correctamente los IDs temporales
            domain = [
                ('materials_list', '=', material.id),
                ('materials_cuantity', '>', 0),
                ('revision', '!=', True),
                ('entregado', '!=', True),
            ]

            # Si la línea actual NO es nueva (tiene un ID real), exclúyela de la búsqueda
            if line.id and isinstance(line.id, int):
                domain.append(('id', '!=', line.id))
            # Si la línea es nueva (es un NewId), no la excluyas por ID (porque no existe en la BD),
            # pero tampoco te preocupes, porque la búsqueda solo encuentra registros guardados.

            apartado_almacen = sum(self.env['dtm.materials.line'].search(domain).mapped('materials_cuantity'))
            disponible_almacen = max(0, stock - apartado_almacen)

            cantidad_solicitada = max(line.materials_cuantity, 0)

            # --- ASIGNACIÓN DE VALORES COMPUTADOS ---
            line.materials_inventory = stock
            if disponible_almacen >= cantidad_solicitada:
                line.materials_availabe = cantidad_solicitada
                line.materials_required = 0
            else:
                line.materials_availabe = disponible_almacen
                line.materials_required = cantidad_solicitada - disponible_almacen

            apartado_almacen = sum(self.env['dtm.materials.line'].search(
                [
                    ('materials_list', '=', material.id),
                    # ('id', '!=', line._origin.id),
                    ('materials_cuantity', '>', 0),
                    ('revision', '!=', True),
                    ('entregado', '!=', True),
                ]).mapped('materials_availabe'))

            # Actualiza el campo 'apartado' del material
            material.apartado = max(apartado_almacen,0)

            # Recalcula el disponible
            material.disponible = material.cantidad - material.apartado


    @api.constrains('materials_cuantity', 'materials_list', 'model_id')
    def _check_materials_exceed_master(self):
        for line in self:
            material = line.materials_list
            if not material or line.model_id.revision_ot == False:
                continue

            get_cot = self.env['dtm.odt'].search([('ot_number', '=', line.model_id.revision_ot)], limit=1)
            if not get_cot:
                continue
            master_qty = get_cot.lista_material_id.filtered_domain([('material_id', '=', material.id)]).cantidad

            if master_qty:  # Solo validar si la orden maestra tiene este material
                get_cot_list = self.env['dtm.odt'].search([('revision_ot', '=', line.model_id.revision_ot)])
                # Suma todas las cantidades de este material en las órdenes hijas (incluyendo la actual)
                total_hijas = sum(
                    item.materials_ids.filtered_domain([('materials_list', '=', material.id)]).materials_cuantity
                    for item in get_cot_list
                )
                if total_hijas > master_qty:
                    raise ValidationError(
                        "La cantidad total solicitada en las órdenes hijas (%s) excede la cantidad disponible en la orden maestra (%s) para el material %s." % (
                            total_hijas, master_qty, material.nombre)
                    )





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
    tipo_servicio = fields.Selection(string="Tipo de Servicio",selection=[("maquinado","Maquinado"),("externo","Maquinado Externo"),("sinquiado","Sinquiado"),("estanado","Estañado"),("pavoneado","Pavoneado"),("anonizado","Anonizado")],required=True)
    cantidad = fields.Integer(string="Cantidad")
    tipo_orden = fields.Char(string="OT/NPI")
    numero_orden = fields.Integer(string="Orden")
    proveedor = fields.Char(string="Proveedor",readonly=True)
    fecha_solicitud = fields.Date(string="Fecha de Solicitud", default= datetime.today(),readonly=True)
    fecha_compra = fields.Date(string="Fecha de Compra",readonly=True)
    fecha_entrada = fields.Date(string="Fecha de Entrada",readonly=True)
    anexos_id = fields.Many2many("ir.attachment")




class OtFile(models.Model):
    _name="dtm.odt.ligas"
    _description = "Modelo para almacenar el archivo de las ligas para el admin"
    model_id = fields.Many2one("dtm.odt")
    model_tubo_id = fields.Many2one("dtm.odt")
    liga = fields.Char(string="Ligas")

class ListaMateriales(models.Model):
    _name = 'dtm.odt.listamateriales'
    _description = 'Modulo para llevar la lista de los materiales para la fabricación del proyecto'

    model_id = fields.Many2one('dtm.odt')

    material_id = fields.Many2one('dtm.materiales')
    cantidad = fields.Integer(string="Cantidad",require=True)
    unitario = fields.Float(string='Unitario',related='material_id.mostrador',store=True,readonly=False)
    precio = fields.Float(string='Total',readonly = True, compute = 'compute_precio')
    currency_id = fields.Many2one('res.currency', string="Moneda", required=True, default=lambda self: self.env.company.currency_id)
    usuario = fields.Char(string="Usuario", compute="_compute_usuario",store=True,readonly=True)

    @api.constrains('cantidad')
    def _check_cantidad(self):
        for record in self:
            if record.cantidad == 0:
                raise ValidationError("La cantidad en el código '%s' no puede ser cero. Por favor, ingrese un valor mayor a cero." % record.material_id.id)



    def _compute_usuario(self):
        for result in self:
            result.usuario = self.env.user.partner_id.email

    @api.depends('cantidad')
    def compute_precio(self):
        for result in self:
            result.precio = result.unitario * result.cantidad



class ConfirmDialog(models.TransientModel):
    _name = 'confirm.dialog.wizard'
    _description = 'Dialogo de Confirmacion'

    message = fields.Text(string="Mensaje")

    def action_close(self):
        return {'type': 'ir.actions.act_window_close'}









