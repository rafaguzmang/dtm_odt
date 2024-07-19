from odoo import api,models,fields
from datetime import datetime
from odoo.exceptions import ValidationError
from fractions import Fraction
import re
import pytz

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
    anexos_id = fields.Many2many("ir.attachment" ,"anexos_id")
    cortadora_id = fields.Many2many("ir.attachment", "cortadora_id",string="Segundas piezas")
    primera_pieza_id = fields.Many2many("ir.attachment", "primera_pieza_id",string="Primeras piezas")
    tubos_id = fields.Many2many("ir.attachment", "tubos_id")
    no_cotizacion = fields.Char('')

    #---------------------Resumen de descripción------------
    description = fields.Text(string="DESCRIPCIÓN")

    #------------------------Notas---------------------------
    notes = fields.Text(string="notes")

    liberado = fields.Char()

    def action_firma_parcial(self):
        self.action_firma(parcial=True)

    def action_firma(self,parcial=False):
        email = self.env.user.partner_id.email
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
        if self.primera_pieza_id or self.cortadora_id: #Agrega los datos a la máquina de corte
            vals = {
                "orden_trabajo":self.ot_number,
                "fecha_entrada": datetime.today(),
                "nombre_orden":self.product_name,
                "tipo_orden": "OT"
            }
            get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT")])
            get_corte_realizado = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT")])
            if not get_corte_realizado:
                if get_corte:
                    get_corte.write(vals)
                else:
                    get_corte.create(vals)
                    get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","OT")])

                lines = [] #Guarda los id de los archivos
                for archivos in get_corte:#Recolecta los archivos que ya fueron cortados para volverlos a cargar
                    for archivo in archivos.cortadora_id:
                        if archivo.estado == "Material cortado":
                            archivo.write({"cortado":True})
                            lines.append(archivo.id)
                get_corte.write({'cortadora_id': [(5, 0, {})]})#limpia la tabla de los archivos

                material_corte = self.primera_pieza_id
                if not self.primera_pieza_id or self.liberado:
                    material_corte = self.cortadora_id

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
                    get_files = self.env['dtm.documentos.cortadora'].search([("nombre","=",file.name),("documentos","=",attachment.datas)],order='nombre desc',limit=1)
                    if get_files:
                        get_files.write(vals)
                        lines.append(get_files.id)
                    else:
                        get_files.create(vals)
                        get_files = self.env['dtm.documentos.cortadora'].search([("nombre","=",file.name),("documentos","=",attachment.datas)],order='nombre desc',limit=1)
                        lines.append(get_files.id)
                    get_corte.write({'cortadora_id': [(6, 0, lines)]})

                lines = []
                get_corte.write({"materiales_id":[(5, 0, {})]})
                for lamina in self.materials_ids:
                    if re.match("Lámina",lamina.nombre):
                        get_almacen = self.env['dtm.materiales'].search([("codigo","=",lamina.materials_list.id)])
                        localizacion = ""
                        if get_almacen.localizacion:
                            localizacion = get_almacen.localizacion
                        content = {
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
                            ("localizacion","=",localizacion)])
                        if get_cortadora_laminas:
                            get_cortadora_laminas.write(content)
                            lines.append(get_cortadora_laminas.id)
                        else:
                            get_cortadora_laminas.create(content)
                            get_cortadora_laminas = self.env['dtm.cortadora.laminas'].search([
                            ("identificador","=",lamina.materials_list.id),("nombre","=",lamina.nombre),
                            ("medida","=",lamina.medida),("cantidad","=",lamina.materials_cuantity),
                            ("inventario","=",lamina.materials_inventory),("requerido","=",lamina.materials_required),
                            ("localizacion","=",localizacion)])
                            lines.append(get_cortadora_laminas.id)
                get_corte.write({"materiales_id":[(6, 0,lines)]})

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
        get_compras = self.env['dtm.compras.requerido'].search([("orden_trabajo","=",self.ot_number)])
        get_realizado = self.env['dtm.compras.realizado'].search([("orden_trabajo","=",self.ot_number)])
        if self.materials_ids:# si la orden contiene materiales ejecuta el código
            for compra in get_compras:#Borra los materiales que esten en compras pero no en la orden
                contiene = False
                for material in self.materials_ids:
                    print(material.materials_list.id,compra.codigo)
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
                print(material.nombre,cantidad)
                if cantidad > 0:
                    vals = {
                        "orden_trabajo":self.ot_number,
                        "codigo":material.materials_list.id,
                        "nombre":material.nombre + medida,
                        "cantidad":cantidad,
                        "disenador":self.firma
                    }
                    get_compras_item = self.env['dtm.compras.requerido'].search([("orden_trabajo","=",self.ot_number),("codigo","=",material.materials_list.id)])
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
    #     for material in get_almdis:
    #         get_ot = self.env['dtm.materials.line'].search([("materials_list","=",material.id)])
    #         get_npi = self.env['dtm.materials.npi'].search([("materials_list","=",material.id)])
    #         if not get_ot and  not get_npi:
    #             print(material.id)
    #             material.unlink()
    #     return res


    #-----------------------Materiales----------------------

class TestModelLine(models.Model):
    _name = "dtm.materials.line"
    _description = "Tabla de materiales"

    model_id = fields.Many2one("dtm.odt")

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
         print(get_almacen,nombre,codigo)
         return  get_almacen

    @api.depends("materials_cuantity")
    def _compute_materials_inventory(self):
        for result in self:
            result.materials_required = 0
            consulta  = result.consultaAlmacen(result.nombre,result.materials_list.id)
            print(consulta)
            if consulta:
                get_almacen = self.env['dtm.materials.line'].search([("materials_list","=",consulta.codigo)])# Busca el material en todas las ordenes para sumar el total de requerido
                cantidad_total = 0 # Guarda las cantidades de materiales solicitadas de todas las ordenes
                consulta_disp = 0 #Guarda las cantidades del material apartado cuando este es igual o mayor al del stock(aparta)
                for item in get_almacen:#obtiene las dos variables anteriores al recorrer la tabla materials.line enfocandose en este item
                    cantidad_total+= item.materials_cuantity
                    consulta_disp += item.materials_availabe
                disp = consulta.cantidad - cantidad_total #Resetea el valor de disponible de la tabla del material correspondiente en el modulo Almacén
                if disp < 0:#Revisa si el dato es menor a cero y de serlo lo restablece a cero
                    disp = 0
                consulta.write({ # Actualiza los valores en la categoria correspondiente del modulo almacén
                    "disponible": disp,
                    "apartado": cantidad_total
                })
                #Hace toda la lógica de calculo
                cantidad = result.materials_cuantity
                inventario = consulta.cantidad
                apartado = result.materials_availabe
                if consulta_disp >= 0 and consulta_disp < inventario:
                    requerido = 0
                    apartado = cantidad
                else:
                    requerido = cantidad - apartado

                if cantidad <= apartado:
                    apartado = cantidad

                if apartado < 0:
                    apartado = 0
                if requerido < 0:
                    requerido = 0

                result.materials_inventory = inventario
                result.materials_availabe = apartado
                self.env['dtm.materials.line'].search([("id","=",self._origin.id)]).write({"materials_availabe":apartado})
                result.materials_required = requerido
                cantidad_total = 0 # Guarda las cantidades de materiales solicitadas de todas las ordenes
                consulta_disp = 0 #Guarda las cantidades del material apartado cuando este es igual o mayor al del stock(aparta)
                for item in get_almacen:#obtiene las dos variables anteriores al recorrer la tabla materials.line enfocandose en este item
                    cantidad_total+= item.materials_cuantity
                    consulta_disp += item.materials_availabe
                disp = consulta.cantidad - cantidad_total #Resetea el valor de disponible de la tabla del material correspondiente en el modulo Almacén
                if disp < 0:#Revisa si el dato es menor a cero y de serlo lo restablece a cero
                    disp = 0
                consulta.write({ # Actualiza los valores en la categoria correspondiente del modulo almacén
                    "disponible": disp,
                    "apartado": cantidad_total
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







