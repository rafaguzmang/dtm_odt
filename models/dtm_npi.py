from odoo import api,models,fields
from datetime import datetime
from odoo.exceptions import ValidationError
import re
import pytz

class NPI(models.Model):
    _name = "dtm.npi"
    _inherit = ['mail.thread']
    _description = "NPI"
    _order = "id desc"

    #---------------------Basicos----------------------

    def action_autoNum(self): # Genera número consecutivo de NPI y OT

        get_odt = self.env['dtm.npi'].search([],order='ot_number desc', limit=1)
        ot_number = get_odt.ot_number + 1
        return ot_number

    status = fields.Char(string="Estado del Producto", readonly=True )
    ot_number = fields.Integer("NÚMERO",default=action_autoNum,  readonly=True )
    tipe_order = fields.Char(strint="NPI", default="NPI",  readonly=True )
    name_client = fields.Many2one("res.partner", string="CLIENTE")
    product_name = fields.Char(string="NOMBRE DEL PRODUCTO")
    date_in = fields.Date(string="FECHA DE ENTRADA",default= datetime.today())
    date_rel = fields.Date(string="FECHA DE ENTREGA",default= datetime.today())
    version_ot = fields.Integer(string="VERSIÓN OT",default=1)
    color = fields.Char(string="COLOR",default="N/A")
    cuantity = fields.Integer(string="CANTIDAD")
    materials_npi_ids = fields.One2many("dtm.materials.npi","model_id",string="Lista")
    firma = fields.Char(string="Firma", readonly = True)
    firma_compras = fields.Char()
    firma_produccion = fields.Char()
    firma_almacen = fields.Char()
    firma_ventas = fields.Char()
    firma_calidad = fields.Char()

    planos = fields.Boolean(string="Planos")
    nesteos = fields.Boolean(string="Nesteos")

    rechazo_id = fields.One2many("dtm.npi.rechazo", "model_id")
    anexos_id = fields.Many2many("ir.attachment","anexos_id_npi")
    cortadora_id = fields.Many2many("ir.attachment", "cortadora_id_npi")
    primera_pieza_id = fields.Many2many("ir.attachment", "npi_id")
    tubos_id = fields.Many2many("ir.attachment", "tubos_id_npi")

    # ---------------------Resumen de descripción------------

    description = fields.Text(string= "DESCRIPCIÓN",placeholder="RESUMEN DE DESCRIPCIÓN")

    #------------------------Notas---------------------------

    notes = fields.Text()

    def action_firma_parcial(self):
        self.action_firma(parcial=True)

    def action_firma(self,parcial=False):
        self.firma = self.env.user.partner_id.name
        get_ot = self.env['dtm.proceso'].search([("ot_number","=",self.ot_number),("tipe_order","=","NPI")])
        get_almacen = self.env['dtm.almacen.odt'].search([("ot_number","=",self.ot_number)])
        vals = {
                "ot_number":self.ot_number,
                "tipe_order":"NPI",
                "name_client":self.name_client.name,
                "product_name":self.product_name,
                "date_in":self.date_in,
                "date_rel":self.date_rel,
                "version_ot":self.version_ot,
                "cuantity":self.cuantity,
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
            get_ot = self.env['dtm.proceso'].search([("ot_number","=",self.ot_number),("tipe_order","=","NPI")])
            get_ot.write(
                {
                    "firma_diseno":self.firma,
                    "status":status
                })
        if get_almacen:
             get_almacen.write({
                "date_in":self.date_in,
                "date_rel":self.date_rel,
                "materials_npi_ids":self.materials_npi_ids
            })
        else:
             get_almacen.create({
                "ot_number":self.ot_number,
                "tipe_order":self.tipe_order,
                "date_in":self.date_in,
                "date_rel":self.date_rel,
                "materials_npi_ids":self.materials_npi_ids,
            })
        get_ot.materials_npi_ids = self.materials_npi_ids
        # get_ot.rechazo_id = self.rechazo_id
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

        # Cortadora laser al modulo proceso
        lines = []
        get_ot.write({'cortadora_id': [(5, 0, {})]})
        for anexo in self.cortadora_id:
            attachment = self.env['ir.attachment'].browse(anexo.id)
            vals = {
                "documentos":attachment.datas,
                "nombre":attachment.name
            }
            get_anexos = self.env['dtm.proceso.cortadora'].search([("nombre","=",attachment.name),("documentos","=",attachment.datas)])
            if get_anexos:
                get_anexos.write(vals)
                lines.append(get_anexos.id)
            else:
                get_anexos.create(vals)
                get_anexos = self.env['dtm.proceso.cortadora'].search([("nombre","=",attachment.name),("documentos","=",attachment.datas)])
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
            get_anexos = self.env['dtm.proceso.tubos'].search([("nombre","=",attachment.name),("documentos","=",attachment.datas)])
            if get_anexos:
                get_anexos.write(vals)
                lines.append(get_anexos.id)
            else:
                get_anexos.create(vals)
                get_anexos = self.env['dtm.proceso.tubos'].search([("nombre","=",attachment.name),("documentos","=",attachment.datas)])
                lines.append(get_anexos.id)
        get_ot.write({'tubos_id': [(6, 0, lines)]})
        self.cortadora_laser()
        self.cortadora_tubos()
        self.compras_odt()

    def cortadora_laser(self):
        if self.primera_pieza_id: #Agrega los datos a la máquina de corte
            vals = {
                "orden_trabajo":self.ot_number,
                "fecha_entrada": datetime.today(),
                "nombre_orden":self.product_name,
                "tipo_orden": "NPI"
            }
            get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","NPI")])
            get_corte_realizado = self.env['dtm.laser.realizados'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","NPI")])
            if not get_corte_realizado:
                if get_corte:
                    get_corte.write(vals)
                else:
                    get_corte.create(vals)
                    get_corte = self.env['dtm.materiales.laser'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","NPI")])

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
                    get_files = self.env['dtm.documentos.cortadora'].search([("nombre","=",file.name),("documentos","=",attachment.datas)])
                    if get_files:
                        get_files.write(vals)
                        lines.append(get_files.id)
                    else:
                        get_files.create(vals)
                        get_files = self.env['dtm.documentos.cortadora'].search([("nombre","=",file.name),("documentos","=",attachment.datas)])
                        lines.append(get_files.id)
                get_corte.write({'cortadora_id': [(6, 0, lines)]})

                lines = []
                get_corte.write({"materiales_id":[(5, 0, {})]})
                for lamina in self.materials_npi_ids:
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
                "tipo_orden": "NPI"
            }
            get_corte = self.env['dtm.tubos.corte'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","NPI")])
            # get_corte_realizado = self.env['dtm.tubos.realizados'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","NPI")])
            # if not get_corte_realizado:
            if get_corte:
                get_corte.write(vals)
            else:
                get_corte.create(vals)
                get_corte = self.env['dtm.tubos.corte'].search([("orden_trabajo","=",self.ot_number),("tipo_orden","=","NPI")])

            lines = []
            get_corte.write({'cortadora_id': [(5, 0, {})]})
            for file in self.tubos_id:
                attachment = self.env['ir.attachment'].browse(file.id)
                vals = {
                    "documentos":attachment.datas,
                    "nombre":attachment.name,
                }
                get_files = self.env['dtm.tubos.documentos'].search([("nombre","=",file.name),("documentos","=",attachment.datas)])
                if get_files:
                    get_files.write(vals)
                    lines.append(get_files.id)
                else:
                    get_files.create(vals)
                    get_files = self.env['dtm.tubos.documentos'].search([("nombre","=",file.name),("documentos","=",attachment.datas)])
                    lines.append(get_files.id)
            get_corte.write({'cortadora_id': [(6, 0, lines)]})

            lines = []
            get_corte.write({"materiales_id":[(5, 0, {})]})
            for material in self.materials_npi_ids: # Busca que coincidan el nombre del material para la busqueda de codigo en su respectivo modelo
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
        print(get_compras)
        for compra in get_compras:
            contiene = False
            for material in self.materials_npi_ids:
                if material.materials_list.id == compra.codigo:
                    contiene = True
            if not contiene:
                compra.unlink()



        for material in self.materials_npi_ids:
            if material.materials_required > 0:
                vals = {
                    "orden_trabajo":self.ot_number,
                    "codigo":material.materials_list.id,
                    "nombre":material.nombre +material.medida,
                    "cantidad":material.materials_required,
                    "disenador":self.firma
                }
                get_compras = self.env['dtm.compras.requerido'].search([("orden_trabajo","=",self.ot_number),("codigo","=",material.materials_list.id)])
                if get_compras:
                    get_compras.write(vals)
                else:
                    get_compras.create(vals)



    def action_imprimir_formato(self): # Imprime según el formato que se esté llenando

            return self.env.ref("dtm_odt.formato_npi").report_action(self)
            # return self.env.ref("dtm_odt.formato_rechazo").report_action(self)

    def action_imprimir_materiales(self): # Imprime según el formato que se esté llenando
        return self.env.ref("dtm_odt.formato_lista_materiales").report_action(self)


    #-----------------------Materiales----------------------

class TestModelLineNPI(models.Model):
    _name = "dtm.materials.npi"
    _description = "Tabla de materiales"

    model_id = fields.Many2one("dtm.npi")

    nombre = fields.Char(compute="_compute_material_list",store=True)
    medida = fields.Char(store=True)

    materials_list = fields.Many2one("dtm.diseno.almacen", string="LISTADO DE MATERIALES")
    materials_cuantity = fields.Integer("CANTIDAD")
    materials_inventory = fields.Integer("INVENTARIO", compute="_compute_materials_inventory", store=True)
    materials_required = fields.Integer("REQUERIDO")

    def consultaAlmacen(self):

        nombre = self.nombre
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
        elif re.match(".*[Rr][oO][dD][aA][mM][iI][eE][nN][tT][oO].*",nombre):
            materiales = self.rodamientos(nombre,medida)
        elif re.match(".*[tT][oO][rR][nN][lL][lL][oO].*",nombre):
            materiales = self.tornillos(nombre,medida)
        elif re.match(".*[tT][uU][bB][oO].*",nombre):
            materiales = self.tubos(nombre,medida)
        elif re.match(".*[vV][aA][rR][iI][lL][lL][aA].*",nombre):
            materiales = self.varillas(nombre,medida)
        else:
            materiales = self.otros(nombre)

        if materiales.exists:
            # print(materiales,materiales.cantidad,materiales.apartado,self.materials_cuantity,self.materials_inventory )
            # print("result B",self.materials_cuantity,self.materials_inventory)
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
            return (materiales.cantidad - sum,materiales,get_almacen,sum)

    def action_materials_list(self):
        pass

    @api.depends("materials_cuantity")
    def _compute_materials_inventory(self):
        for result in self:
            try:
                consulta  = self.consultaAlmacen()

                result.materials_required = 0
                cantidad = result.materials_cuantity
                inventario = consulta[0]
                if inventario <=0:
                    inventario = 0
                if cantidad <= inventario:
                    result.materials_inventory = cantidad
                else:
                    result.materials_inventory = inventario
                    result.materials_required = cantidad - inventario

                requerido = result.materials_required
                if requerido > 0: # Manda comprar el material si este ya no hay en el almacén
                    get_odt = self.env['dtm.npi'].search([])
                    for get in get_odt:
                        for id in get.materials_npi_ids:
                            if result._origin.id == id.id:
                                orden = "NPI-"+ str(get.ot_number)

                    nombre = result.materials_list.nombre
                    if result.materials_list.medida:
                        nombre = result.materials_list.nombre +" " + result.materials_list.medida

                    descripcion = result.materials_list.caracteristicas
                    if not descripcion:
                        descripcion = ""
                    get_requerido = self.env['dtm.compras.requerido'].search([("orden_trabajo","=",str(orden)),("nombre","=",nombre)])

                    if not get_requerido:
                        self.env.cr.execute("INSERT INTO dtm_compras_requerido(orden_trabajo,nombre,cantidad,description) VALUES('"+str(orden)+"', '"+nombre+"', "+str(requerido)+", '"+descripcion+"')")
                    else:
                        self.env.cr.execute("UPDATE dtm_compras_requerido SET cantidad="+ str(requerido)+" WHERE orden_trabajo='"+str(orden)+"' and nombre='"+nombre+"'")
                    if requerido <= 0:
                        self.env.cr.execute("DELETE FROM dtm_compras_requerido WHERE cantidad = 0")

                if cantidad <= 0:
                    result.materials_cuantity = 0
                    result.materials_inventory = 0
                    result.materials_required = 0
                if inventario < 0:
                    result.materials_inventory = 0

                disponible = consulta[1].cantidad - (consulta[3] + cantidad)
                if disponible < 0:
                    disponible = 0


                vals = {
                    "apartado": consulta[3]+cantidad,
                    "disponible": disponible
                }
                consulta[1].write(vals)
                vals = {
                    "cantidad": disponible
                }
                consulta[2].write(vals)
            except:
                print("Error en consulta")

    @api.depends("materials_list")
    def _compute_material_list(self):
        for result in self:
            result.nombre = result.materials_list.nombre
            result.medida = result.materials_list.medida

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
                # print(nombre,calibre,largo,ancho)
                get_nombre = self.env['dtm.nombre.material'].search([("nombre","=",nombre)]).id
                get_material = self.env['dtm.materiales'].search([("material_id","=",get_nombre),("calibre","=",calibre),("largo","=",largo),("ancho","=",ancho)])

                return get_material

    def angulos(self,nombre,medida):
        nombre = re.sub("^\s+","",nombre)
        nombre = nombre[nombre.index(" "):]
        nombre = re.sub("^\s+", "", nombre)
        nombre = re.sub("\s+$", "", nombre)
        # print("result 1",nombre,medida)
        if  medida.find(" x ") >= 0 or medida.find(" X "):
            if medida.find(" @ ") >= 0:
                # print(nombre)
                # nombre = nombre[len("Lámina "):len(nombre)-1]
                calibre = medida[medida.index("@")+2:medida.index(",")]
                medida = re.sub("X","x",medida)
                # print(medida)
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
        # print("result 1",nombre,medida)
        if  medida.find(" x ") >= 0 or medida.find(" X "):
            if medida.find(" espesor ") >= 0:
                # print(nombre)
                # nombre = nombre[len("Lámina "):len(nombre)-1]
                calibre = medida[medida.index("espesor")+len("espesor"):medida.index(",")]
                medida = re.sub("X","x",medida)
                # print(calibre)
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
        # print("result 1",nombre,medida)
        if  medida.find(" x ") >= 0 or medida.find(" X "):
            if medida.find("@") >= 0:
                # print(nombre)
                # nombre = nombre[len("Lámina "):len(nombre)-1]
                # print(medida)
                calibre = medida[medida.index("@")+len("@"):medida.index(",")]
                medida = re.sub("X","x",medida)
                # print(calibre)
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
            # print("result 1",nombre,medida)
            if  medida.find(" x ") >= 0 or medida.find(" X "):
                if medida.find(" @ ") >= 0:
                    # print(nombre)
                    # nombre = nombre[len("Lámina "):len(nombre)-1]
                    calibre = medida[medida.index("@")+2:]
                    medida = re.sub("X","x",medida)
                    # print(medida)
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
                    # print(calibre)
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
            # print("result 1",nombre,medida)
            if medida.find(" x ") >= 0 or medida.find(" X "):
                if medida.find("@") >= 0:
                    # print(nombre)
                    # nombre = nombre[len("Lámina "):len(nombre)-1]
                    calibre = medida[medida.index("@")+len("@"):]
                    medida = re.sub("X","x",medida)
                    # print(calibre)
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

                    # print(nombre,diametro,largo)
                    # Busca coincidencias entre el almacen y el aréa de diseno dtm_diseno_almacen
                    get_mid = self.env['dtm.tubos.nombre'].search([("nombre","=",nombre)]).id
                    get_angulo = self.env['dtm.materiales.tubos'].search([("material_id","=",get_mid),("diametro","=",float(diametro)),("largo","=",float(largo)),("calibre","=",float(calibre))])

    def varillas(self,nombre,medida):
            nombre = re.sub("^\s+","",nombre)
            nombre = nombre[nombre.index(" "):]
            nombre = re.sub("^\s+","",nombre)
            nombre = re.sub("\s+$","",nombre)
            medida = re.sub("^\s+","",medida)
            medida = re.sub("\s+$","",medida)
            if  medida.find(" x ") >= 0 or medida.find(" X "):
                    medida = re.sub("X","x",medida)
                    # print(calibre)
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


class Rechazo(models.Model):
    _name = "dtm.npi.rechazo"
    _description = "Tabla para llenar los motivos por el cual se rechazo el NPI"

    model_id = fields.Many2one("dtm.npi")

    descripcion = fields.Text(string="Descripción del Rechazo")
    fecha = fields.Date(string="Fecha")
    hora = fields.Char(string="Hora")
    firma = fields.Char(string="Firma", default="Diseño")

    @api.onchange("fecha")
    def _action_fecha(self):
        self.fecha = datetime.now()

        self.hora = datetime.now(pytz.timezone('America/Mexico_City')).strftime("%H:%M")






        


