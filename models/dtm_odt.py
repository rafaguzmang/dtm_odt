from odoo import api,models,fields
from datetime import datetime
from odoo.exceptions import ValidationError
from fractions import Fraction
import re
import pytz

class DtmOdt(models.Model):
    _name = "dtm.odt"
    _description = "Oden de trabajo"
    _order = "ot_number desc"

    #---------------------Basicos----------------------

    status = fields.Char(readonly=True)
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
    firma = fields.Char(string="Firma", readonly = True)
    firma_compras = fields.Char()
    firma_produccion = fields.Char()
    firma_almacen = fields.Char()
    firma_ventas = fields.Char()
    firma_calidad = fields.Char()

    planos = fields.Boolean(string="Planos",default=False)
    nesteos = fields.Boolean(string="Nesteos",default=False)

    rechazo_id = fields.One2many("dtm.odt.rechazo", "model_id")
    anexos_id = fields.Many2many("ir.attachment" ,"anexos_id")
    cortadora_id = fields.Many2many("ir.attachment", "cortadora_id",string="Segundas piezas")
    primera_pieza_id = fields.Many2many("ir.attachment", "primera_pieza_id",string="Primeras piezas")
    tubos_id = fields.Many2many("ir.attachment", "tubos_id")

    #---------------------Resumen de descripción------------

    description = fields.Text(string="DESCRIPCIÓN")

    #------------------------Notas---------------------------

    notes = fields.Text(string="notes")

    def action_firma_parcial(self):
        self.action_firma(parcial=True)

    def action_firma(self,parcial=False):
        self.firma = self.env.user.partner_id.name
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
            get_anexos = self.env['dtm.proceso.anexos'].search([("nombre","=",attachment.name)])
            if get_anexos:
                get_anexos.write(vals)
                lines.append(get_anexos.id)
            else:
                get_anexos.create(vals)
                get_anexos = self.env['dtm.proceso.anexos'].search([("nombre","=",attachment.name)])
                lines.append(get_anexos.id)
        get_ot.write({'anexos_id': [(6, 0, lines)]})
        lines = []
        get_ot.write({'primera_pieza_id': [(5, 0, {})]})
        for anexo in self.primera_pieza_id:
            attachment = self.env['ir.attachment'].browse(anexo.id)
            vals = {
                "documentos":attachment.datas,
                "nombre":attachment.name
            }
            get_anexos = self.env['dtm.proceso.primer'].search([("nombre","=",attachment.name)])
            if get_anexos:
                get_anexos.write(vals)
                lines.append(get_anexos.id)
            else:
                get_anexos.create(vals)
                get_anexos = self.env['dtm.proceso.primer'].search([("nombre","=",attachment.name)])
                lines.append(get_anexos.id)
        get_ot.write({'primera_pieza_id': [(6, 0, lines)]})

        # Cortadora laser al modulo proceso
        lines = []
        get_ot.write({'cortadora_id': [(5, 0, {})]})
        for anexo in self.cortadora_id:
            attachment = self.env['ir.attachment'].browse(anexo.id)
            vals = {
                "documentos":attachment.datas,
                "nombre":attachment.name
            }
            get_anexos = self.env['dtm.proceso.cortadora'].search([("nombre","=",attachment.name)])
            if get_anexos:
                get_anexos.write(vals)
                lines.append(get_anexos.id)
            else:
                get_anexos.create(vals)
                get_anexos = self.env['dtm.proceso.cortadora'].search([("nombre","=",attachment.name)])
                lines.append(get_anexos.id)
        get_ot.write({'cortadora_id': [(6, 0, lines)]})
        # Cortadora de tubos al modulo proceso
        get_ot.write({'tubos_id': [(5, 0, {})]})
        lines = []
        for anexo in self.tubos_id:
            attachment = self.env['ir.attachment'].browse(anexo.id)
            vals = {
                "documentos":attachment.datas,
                "nombre":attachment.name,
            }
            get_anexos = self.env['dtm.proceso.tubos'].search([("nombre","=",attachment.name)])
            if get_anexos:
                get_anexos.write(vals)
                lines.append(get_anexos.id)
            else:
                get_anexos.create(vals)
                get_anexos = self.env['dtm.proceso.tubos'].search([("nombre","=",attachment.name)])
                lines.append(get_anexos.id)
        get_ot.write({'tubos_id': [(6, 0, lines)]})

        self.cortadora_laser()
        self.cortadora_tubos()
        # self.compras_odt()

    def cortadora_laser(self):
        if self.primera_pieza_id: #Agrega los datos a la máquina de corte
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

                lines = []
                for archivos in get_corte:
                    for archivo in archivos.cortadora_id:
                        if archivo.estado == "Material cortado":
                            archivo.write({"cortado":True})
                            lines.append(archivo.id)
                get_corte.write({'cortadora_id': [(5, 0, {})]})
                for file in self.primera_pieza_id:
                    attachment = self.env['ir.attachment'].browse(file.id)
                    vals = {
                        "documentos":attachment.datas,
                        "nombre":attachment.name,
                        "primera_pieza":True
                    }
                    get_files = self.env['dtm.documentos.cortadora'].search([("nombre","=",file.name)])
                    if get_files:
                        get_files.write(vals)
                        lines.append(get_files.id)
                    else:
                        get_files.create(vals)
                        get_files = self.env['dtm.documentos.cortadora'].search([("nombre","=",file.name)])
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
                get_files = self.env['dtm.tubos.documentos'].search([("nombre","=",file.name)])
                if get_files:
                    get_files.write(vals)
                    lines.append(get_files.id)
                else:
                    get_files.create(vals)
                    get_files = self.env['dtm.tubos.documentos'].search([("nombre","=",file.name)])
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

    # def compras_odt(self):
    #     get_compras = self.env['dtm.compras.requerido'].search([("orden_trabajo","=",self.ot_number)])
    #     if get_compras:
    #         for compra in get_compras:
    #             for material in self.materials_ids:
    #
    #                 if(compra.codigo==material.materials_list.id and material.materials_required>0):
    #                     print(compra.codigo,material.materials_list.id)
    #                     break
    #
    #
    #      # for material in self.materials_ids:
    #      #    if material.materials_required > 0:
    #      #        val = {
    #      #            "orden_trabajo":self.ot_number,
    #      #            "codigo":material.materials_list.id,
    #      #            "nombre":material.nombre +material.medida,
    #      #            "cantidad":material.materials_required,
    #      #            "disenador":self.firma
    #      #        }
    #      #        get_compras = self.env['dtm.compras.requerido'].search([("orden_trabajo","=",self.ot_number)])
    #      #        for compra in get_compras:
    #      #
    #      #        print(get_compras)

    def action_imprimir_formato(self): # Imprime según el formato que se esté llenando
        return self.env.ref("dtm_odt.formato_orden_de_trabajo").report_action(self)

    def action_imprimir_materiales(self): # Imprime según el formato que se esté llenando
        return self.env.ref("dtm_odt.formato_lista_materiales").report_action(self)


    #-----------------------Materiales----------------------

class TestModelLine(models.Model):
    _name = "dtm.materials.line"
    _description = "Tabla de materiales"

    model_id = fields.Many2one("dtm.odt")

    nombre = fields.Char(compute="_compute_material_list",store=True)
    medida = fields.Char(store=True)

    materials_list = fields.Many2one("dtm.diseno.almacen", string="LISTADO DE MATERIALES",required=True)
    materials_cuantity = fields.Integer("CANTIDAD")
    materials_inventory = fields.Integer("INVENTARIO", compute="_compute_materials_inventory", store=True)
    materials_required = fields.Integer("REQUERIDO")

    def action_materials_list(self):
        pass

    def materiales(self,nombre,medida):
        nombre = re.sub("^\s+","",nombre)
        nombre = nombre[nombre.index(" "):]
        nombre = re.sub("^\s+", "", nombre)
        nombre = re.sub("\s+$", "", nombre)
        if  medida.find(" x ") >= 0 or medida.find(" X "):
            if medida.find(" @ ") >= 0:
                calibre = medida[medida.index("@")+2:]
                medida = re.sub("X","x",medida)
                if medida.find("x"):
                    largo = medida[:medida.index("x")-1]
                    ancho = medida[medida.index("x")+2:medida.index("@")]
                regx = re.match("\d+/\d+", calibre)
                if regx:
                    calibre = float(calibre[0:calibre.index("/")]) / float(calibre[calibre.index("/") + 1:len(calibre)])
                regx = re.match("\d+/\d+", largo)
                if regx:
                    largo = float(largo[0:largo.index("/")]) / float(largo[largo.index("/") + 1:len(largo)])
                regx = re.match("\d+/\d+", ancho)
                if regx:
                    ancho = float(ancho[0:ancho.index("/")]) / float(ancho[ancho.index("/") + 1:len(ancho)])

                get_nombre = self.env['dtm.nombre.material'].search([("nombre","=",nombre)]).id
                get_material = self.env['dtm.materiales'].search([("material_id","=",get_nombre),("calibre","=",calibre),("largo","=",largo),("ancho","=",ancho)])

                return get_material

    def angulos(self,nombre,medida):
        nombre = re.sub("^\s+","",nombre)
        nombre = nombre[nombre.index(" "):]
        nombre = re.sub("^\s+", "", nombre)
        nombre = re.sub("\s+$", "", nombre)

        if  medida.find(" x ") >= 0 or medida.find(" X "):
            if medida.find(" @ ") >= 0:

                # nombre = nombre[len("Lámina "):len(nombre)-1]
                calibre = medida[medida.index("@")+2:medida.index(",")]
                medida = re.sub("X","x",medida)

                if medida.find("x"):
                    alto = medida[:medida.index("x")-1]
                    ancho = medida[medida.index("x")+2:medida.index("@")]
                    largo = medida[medida.index(",")+1:]

                # Convierte fracciones a decimales
                regx = re.match("\d+/\d+", calibre)
                if regx:
                    calibre = float(calibre[0:calibre.index("/")]) / float(calibre[calibre.index("/") + 1:len(calibre)])
                regx = re.match("\d+/\d+", largo)
                if regx:
                    largo = float(largo[0:largo.index("/")]) / float(largo[largo.index("/") + 1:len(largo)])
                regx = re.match("\d+/\d+", ancho)
                if regx:
                    ancho = float(ancho[0:ancho.index("/")]) / float(ancho[ancho.index("/") + 1:len(ancho)])
                regx = re.match("\d+/\d+", alto)
                if regx:
                    alto = float(ancho[0:ancho.index("/")]) / float(ancho[ancho.index("/") + 1:len(ancho)])
                # Busca coincidencias entre el almacen y el aréa de diseno dtm_diseno_almacen
                get_mid = self.env['dtm.angulos.nombre'].search([("nombre","=",nombre)]).id
                get_angulo = self.env['dtm.materiales.angulos'].search([("material_id","=",get_mid),("calibre","=",float(calibre)),("largo","=",float(largo)),("ancho","=",float(ancho)),("alto","=",float(alto))])
                return  get_angulo

    def canales(self,nombre,medida):
        nombre = re.sub("^\s+","",nombre)
        nombre = nombre[nombre.index(" "):]
        nombre = re.sub("^\s+", "", nombre)
        nombre = re.sub("\s+$", "", nombre)

        if  medida.find(" x ") >= 0 or medida.find(" X "):
            if medida.find(" espesor ") >= 0:

                # nombre = nombre[len("Lámina "):len(nombre)-1]
                calibre = medida[medida.index("espesor")+len("espesor"):medida.index(",")]
                medida = re.sub("X","x",medida)

                if medida.find("x"):
                    alto = medida[:medida.index("x")-1]
                    ancho = medida[medida.index("x")+2:medida.index("espesor")]
                    largo = medida[medida.index(",")+1:]

                # Convierte fracciones a decimales
                regx = re.match("\d+/\d+", calibre)
                if regx:
                    calibre = float(calibre[0:calibre.index("/")]) / float(calibre[calibre.index("/") + 1:len(calibre)])
                regx = re.match("\d+/\d+", largo)
                if regx:
                    largo = float(largo[0:largo.index("/")]) / float(largo[largo.index("/") + 1:len(largo)])
                regx = re.match("\d+/\d+", ancho)
                if regx:
                    ancho = float(ancho[0:ancho.index("/")]) / float(ancho[ancho.index("/") + 1:len(ancho)])
                regx = re.match("\d+/\d+", alto)
                if regx:
                    alto = float(ancho[0:ancho.index("/")]) / float(ancho[ancho.index("/") + 1:len(ancho)])

                # Busca coincidencias entre el almacen y el aréa de diseno dtm_diseno_almacen
                get_mid = self.env['dtm.canal.nombre'].search([("nombre","=",nombre)]).id
                get_angulo = self.env['dtm.materiales.canal'].search([("material_id","=",get_mid),("espesor","=",float(calibre)),("largo","=",float(largo)),("ancho","=",float(ancho)),("alto","=",float(alto))])
                return get_angulo

    def perfiles(self,nombre,medida):
        nombre = re.sub("^\s+","",nombre)
        nombre = nombre[nombre.index(" "):]
        nombre = re.sub("^\s+", "", nombre)
        nombre = re.sub("\s+$", "", nombre)

        if  medida.find(" x ") >= 0 or medida.find(" X "):
            if medida.find("@") >= 0:

                # nombre = nombre[len("Lámina "):len(nombre)-1]

                calibre = medida[medida.index("@")+len("@"):medida.index(",")]
                medida = re.sub("X","x",medida)

                if medida.find("x"):
                    alto = medida[:medida.index("x")-1]
                    ancho = medida[medida.index("x")+2:medida.index(" @ ")]
                    largo = medida[medida.index(",")+1:]

                # Convierte fracciones a decimales
                regx = re.match("\d+/\d+", calibre)
                if regx:
                    calibre = float(calibre[0:calibre.index("/")]) / float(calibre[calibre.index("/") + 1:len(calibre)])
                regx = re.match("\d+/\d+", largo)
                if regx:
                    largo = float(largo[0:largo.index("/")]) / float(largo[largo.index("/") + 1:len(largo)])
                regx = re.match("\d+/\d+", ancho)
                if regx:
                    ancho = float(ancho[0:ancho.index("/")]) / float(ancho[ancho.index("/") + 1:len(ancho)])
                regx = re.match("\d+/\d+", alto)
                if regx:
                    alto = float(ancho[0:ancho.index("/")]) / float(ancho[ancho.index("/") + 1:len(ancho)])

                # Busca coincidencias entre el almacen y el aréa de diseno dtm_diseno_almacen
                get_mid = self.env['dtm.perfiles.nombre'].search([("nombre","=",nombre)]).id
                get_angulo = self.env['dtm.materiales.perfiles'].search([("material_id","=",get_mid),("calibre","=",float(calibre)),("largo","=",float(largo)),("ancho","=",float(ancho)),("alto","=",float(alto))])
                return get_angulo

    def pintura(self,nombre,medida):
        nombre = re.sub("^\s+","",nombre)
        nombre = nombre[nombre.index(" "):]
        nombre = re.sub("^\s+","",nombre)
        nombre = re.sub("\s+$","",nombre)
        medida = re.sub("^\s+","",medida)
        medida = re.sub("\s+$","",medida)
        get_mid = self.env['dtm.pintura.nombre'].search([("nombre","=",nombre)]).id
        get_angulo = self.env['dtm.materiales.pintura'].search([("material_id","=",get_mid),("cantidades","=",medida)])
        return get_angulo

    def rodamientos(self,nombre):
        nombre = re.sub("^\s+","",nombre)
        nombre = nombre[nombre.index(" "):]
        nombre = re.sub("^\s+","",nombre)
        nombre = re.sub("\s+$","",nombre)
        get_mid = self.env['dtm.rodamientos.nombre'].search([("nombre","=",nombre)]).id
        get_angulo = self.env['dtm.materiales.rodamientos'].search([("material_id","=",get_mid)])
        return get_angulo

    def solera(self,nombre,medida):
         if  re.match(".*[sS][oO][lL][eE][rR][aA].*",nombre):
            nombre = re.sub("^\s+","",nombre)
            nombre = nombre[nombre.index(" "):]
            nombre = re.sub("^\s+", "", nombre)
            nombre = re.sub("\s+$", "", nombre)

            if  medida.find(" x ") >= 0 or medida.find(" X "):
                if medida.find(" @ ") >= 0:

                    # nombre = nombre[len("Lámina "):len(nombre)-1]
                    calibre = medida[medida.index("@")+2:]
                    medida = re.sub("X","x",medida)

                    if medida.find("x"):
                        largo = medida[:medida.index("x")-1]
                        ancho = medida[medida.index("x")+2:medida.index("@")]
                    # Convierte fracciones a decimales
                    regx = re.match("\d+/\d+", calibre)
                    if regx:
                        calibre = float(calibre[0:calibre.index("/")]) / float(calibre[calibre.index("/") + 1:len(calibre)])
                    regx = re.match("\d+/\d+", largo)
                    if regx:
                        largo = float(largo[0:largo.index("/")]) / float(largo[largo.index("/") + 1:len(largo)])
                    regx = re.match("\d+/\d+", ancho)
                    if regx:
                        ancho = float(ancho[0:ancho.index("/")]) / float(ancho[ancho.index("/") + 1:len(ancho)])
                    get_mid = self.env['dtm.solera.nombre'].search([("nombre","=",nombre)]).id
                    get_solera = self.env['dtm.materiales.solera'].search([("material_id","=",get_mid),("calibre","=",float(calibre)),("largo","=",float(largo)),("ancho","=",float(ancho))])
                    return get_solera

    def tornillos(self,nombre,medida):
            nombre = re.sub("^\s+","",nombre)
            nombre = nombre[nombre.index(" "):]
            nombre = re.sub("^\s+","",nombre)
            nombre = re.sub("\s+$","",nombre)
            medida = re.sub("^\s+","",medida)
            medida = re.sub("\s+$","",medida)
            if  medida.find(" x ") >= 0 or medida.find(" X "):
                    medida = re.sub("X","x",medida)

                    if medida.find("x"):
                        diametro = medida[:medida.index("x")-1]
                        largo = medida[medida.index("x")+1:]

                    # Convierte fracciones a decimales
                    regx = re.match("\d+/\d+", diametro)
                    if regx:
                        diametro = float(diametro[0:diametro.index("/")]) / float(diametro[diametro.index("/") + 1:len(diametro)])
                    regx = re.match("\d+/\d+", largo)
                    if regx:
                        largo = float(largo[0:largo.index("/")]) / float(largo[largo.index("/") + 1:len(largo)])

                    get_mid = self.env['dtm.tornillos.nombre'].search([("nombre","=",nombre)]).id
                    get_angulo = self.env['dtm.materiales.tornillos'].search([("material_id","=",get_mid),("diametro","=",float(diametro)),("largo","=",float(largo))])
                    return get_angulo

    def tubos(self,nombre,medida):
         if re.match(".*[tT][uU][bB][oO].*",nombre):
            nombre = re.sub("^\s+","",nombre)
            nombre = nombre[nombre.index(" "):]
            nombre = re.sub("^\s+", "", nombre)
            nombre = re.sub("\s+$", "", nombre)

            if medida.find(" x ") >= 0 or medida.find(" X "):
                if medida.find("@") >= 0:

                    # nombre = nombre[len("Lámina "):len(nombre)-1]
                    calibre = medida[medida.index("@")+len("@"):]
                    medida = re.sub("X","x",medida)

                    if medida.find("x"):
                        diametro = medida[:medida.index("x")-1]
                        largo = medida[medida.index("x")+2:medida.index("@")]

                    # Convierte fracciones a decimales
                    regx = re.match("\d+/\d+", calibre)
                    if regx:
                        calibre = float(calibre[0:calibre.index("/")]) / float(calibre[calibre.index("/") + 1:len(calibre)])
                    regx = re.match("\d+/\d+", largo)
                    if regx:
                        largo = float(largo[0:largo.index("/")]) / float(largo[largo.index("/") + 1:len(largo)])
                    regx = re.match("\d+/\d+", diametro)
                    if regx:
                        diametro = float(diametro[0:diametro.index("/")]) / float(diametro[diametro.index("/") + 1:len(diametro)])


                    # Busca coincidencias entre el almacen y el aréa de diseno dtm_diseno_almacen
                    get_mid = self.env['dtm.tubos.nombre'].search([("nombre","=",nombre)]).id
                    get_angulo = self.env['dtm.materiales.tubos'].search([("material_id","=",get_mid),("diametro","=",float(diametro)),("largo","=",float(largo)),("calibre","=",float(calibre))])
                    return get_angulo

    def varillas(self,nombre,medida):
            nombre = re.sub("^\s+","",nombre)
            nombre = nombre[nombre.index(" "):]
            nombre = re.sub("^\s+","",nombre)
            nombre = re.sub("\s+$","",nombre)
            medida = re.sub("^\s+","",medida)
            medida = re.sub("\s+$","",medida)
            if  medida.find(" x ") >= 0 or medida.find(" X "):
                    medida = re.sub("X","x",medida)

                    if medida.find("x"):
                        diametro = medida[:medida.index("x")-1]
                        largo = medida[medida.index("x")+1:]
                    # Convierte fracciones a decimales
                    regx = re.match("\d+/\d+", diametro)
                    if regx:
                        diametro = float(diametro[0:diametro.index("/")]) / float(diametro[diametro.index("/") + 1:len(diametro)])
                    regx = re.match("\d+/\d+", largo)
                    if regx:
                        largo = float(largo[0:largo.index("/")]) / float(largo[largo.index("/") + 1:len(largo)])
                    get_mid = self.env['dtm.varilla.nombre'].search([("nombre","=",nombre)]).id
                    get_angulo = self.env['dtm.materiales.varilla'].search([("material_id","=",get_mid),("diametro","=",float(diametro)),("largo","=",float(largo))])
                    return get_angulo

    def otros(self,nombre):
        nombre = re.sub("^\s+","",nombre)
        nombre = re.sub("\s+$","",nombre)

        get_mid = self.env['dtm.otros.nombre'].search([("nombre","=",nombre)]).id
        get_angulo = self.env['dtm.materiales.otros'].search([("nombre_id","=",get_mid)])
        return get_angulo

    def consultaAlmacen(self):

        nombre = str(self.nombre)
        medida = self.medida

        if re.match(".*[Ll][aáAÁ][mM][iI][nN][aA].*",nombre):
            materiales = self.materiales(nombre,medida)
        elif re.match(".*[aáAÁ][nN][gG][uU][lL][oO][sS]*.*",nombre):
            materiales = self.angulos(nombre,medida)
        elif re.match(".*[cC][aA][nN][aA][lL].*",nombre):
             materiales = self.canales(nombre,medida)
        elif re.match(".*[pP][eE][rR][fF][iI][lL].*",nombre):
             materiales = self.perfiles(nombre,medida)
        elif re.match(".*[pP][iI][nN][tT][uU][rR][aA].*",nombre):
             materiales = self.pintura(nombre,medida)
        elif re.match(".*[Rr][oO][dD][aA][mM][iI][eE][nN][tT][oO].*",nombre):
            materiales = self.rodamientos(nombre)
        elif re.match(".*[tT][oO][rR][nN][lL][lL][oO].*",nombre):
            materiales = self.tornillos(nombre,medida)
        elif re.match(".*[tT][uU][bB][oO].*",nombre):
            materiales = self.tubos(nombre,medida)
        elif re.match(".*[vV][aA][rR][iI][lL][lL][aA].*",nombre):
            materiales = self.varillas(nombre,medida)
        else:
            materiales = self.otros(nombre)

        cantidad_materiales = 0
        if materiales:
           cantidad_materiales = materiales.cantidad
        get_odt = self.env['dtm.materials.line'].search([("nombre","=",self.nombre),("medida","=",self.medida)])
        get_npi = self.env['dtm.materials.npi'].search([("nombre","=",self.nombre),("medida","=",self.medida)])
        get_almacen = self.env['dtm.diseno.almacen'].search([("nombre","=",self.nombre),("medida","=",self.medida)])

        sum = 0
        for result in get_odt:
            if result.id != self._origin.id:
                sum += result.materials_cuantity
        for result in get_npi:
            if result.id != self._origin.id:
                sum += result.materials_cuantity

        return (cantidad_materiales - sum,materiales,get_almacen,sum)

    @api.depends("materials_cuantity")
    def _compute_materials_inventory(self):
        for result in self:
            # try:
                consulta  = self.consultaAlmacen()

                result.materials_required = 0
                cantidad = result.materials_cuantity
                inventario = consulta[0]
                if inventario < 0:
                    inventario = 0
                if cantidad <= inventario:
                    result.materials_inventory = cantidad
                else:
                    result.materials_inventory = inventario
                    result.materials_required = cantidad - inventario
                requerido = result.materials_required

                # if requerido > 0:# Manda la solicitud de compra del material requerido
                #     get_odt = self.env['dtm.odt'].search([])#Obtiene el número de la orden de trabajo
                #     for get in get_odt:
                #         for id in get.materials_ids:
                #             if result._origin.id == id.id:
                #                 orden = get.ot_number
                #
                #     nombre = result.materials_list.nombre
                #     if result.materials_list.medida:
                #         nombre = result.materials_list.nombre +" " + result.materials_list.medida
                #         item_id = result.materials_list.id
                #
                #     descripcion = ""
                #     if descripcion:
                #         descripcion = result.materials_list.caracteristicas
                #
                #     get_requerido = self.env['dtm.compras.requerido'].search([("orden_trabajo","=",orden),("nombre","=",nombre)])
                #
                #     if not get_requerido:
                #         self.env.cr.execute("INSERT INTO dtm_compras_requerido(orden_trabajo,nombre,cantidad,codigo) VALUES('"+str(orden)+"', '"+nombre+"', "+str(requerido)+",'"+ str(item_id)+"')")
                #     else:
                #         self.env.cr.execute("UPDATE dtm_compras_requerido SET cantidad="+ str(requerido)+" WHERE orden_trabajo='"+str(orden)+"' and nombre='"+nombre+"'")
                #     if requerido <= 0:
                #         self.env.cr.execute("DELETE FROM dtm_compras_requerido WHERE cantidad = 0")
                #
                # if cantidad <= 0:
                #     result.materials_cuantity = 0
                #     result.materials_inventory = 0
                #     result.materials_required = 0
                #
                # if inventario < 0:
                #     result.materials_inventory = 0
                #
                # disponible = 0
                # if consulta[1]:
                #     disponible = consulta[1].cantidad - (consulta[3] + cantidad)
                #
                # if disponible < 0:
                #     disponible = 0
                #
                # vals = {
                #     "apartado": consulta[3]+cantidad,
                #     "disponible": disponible
                # }
                # if consulta[1]:
                #
                #     consulta[1].write(vals)
                # vals = {
                #     "cantidad": disponible
                # }
                # consulta[2].write(vals)
            # except:
            #     print("Error en consulta")

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









