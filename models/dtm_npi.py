from odoo import api,models,fields
from datetime import datetime
from odoo.exceptions import ValidationError
import re



class NPI(models.Model):
    _name = "dtm.npi"
    _description = "NPI"
    # _order = "ot_number desc"
   
    #---------------------Basicos----------------------

    status = fields.Char(string="Estado del Producto", readonly=True )
    sequence = fields.Integer()
    ot_number = fields.Integer("NÚMERO",default="000",  readonly=True )
    tipe_order = fields.Char(strint="NPI", default="NPI",  readonly=True )
    name_client = fields.Many2one("res.partner", string="CLIENTE")
    product_name = fields.Char(string="NOMBRE DEL PRODUCTO")
    date_in = fields.Date(string="FECHA DE ENTRADA",default= datetime.today())
    date_rel = fields.Date(string="FECHA DE ENTREGA",default= datetime.today())
    version_ot = fields.Integer(string="VERSIÓN OT",default=1)
    color = fields.Char(string="COLOR",default="N/A")
    cuantity = fields.Integer(string="CANTIDAD")
    materials_ids = fields.One2many("dtm.materials.npi","model_id",string="Lista")
    firma = fields.Char(string="Firma", readonly = True)

    planos = fields.Boolean(string="Planos")
    nesteos = fields.Boolean(string="Nesteos")

    rechazo_id = fields.One2many("dtm.npi.rechazo", "model_id")

    anexos_id = fields.Many2many("ir.attachment")
    cortadora_id = fields.Many2many("dtm.documentos.cortadora")
    tubos_id = fields.Many2many("dtm.documentos.tubos")

    # ---------------------Resumen de descripción------------

    description = fields.Text(string= "DESCRIPCIÓN",placeholder="RESUMEN DE DESCRIPCIÓN")

    #------------------------Notas---------------------------

    notes = fields.Text()

    def action_firma(self):
        self.firma = self.env.user.partner_id.name

        get_ot = self.env['dtm.proceso'].search([("ot_number","=",self.ot_number),("tipe_order","=","NPI")])
        print(get_ot)
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
                "planos":self.planos,
                "nesteos":self.nesteos,
                "notes":self.notes,
                "color":self.color,
                "firma":self.firma
        }
        method = 1
        if get_ot:
            print("Upload")
            get_ot.write(vals)
        else:
            get_ot.create(vals)
            method = 0

        lines = []
        for material in self.materials_ids:
            datos = {
                "nombre":material.nombre,
                "medida":material.medida,
                "materials_cuantity":material.materials_cuantity,
                "materials_inventory":material.materials_inventory,
                "materials_required":material.materials_required
            }
            if self.env['dtm.proceso.materials'].search([("nombre","=",material.nombre),("medida","=",material.medida)] ):
                line = (1,get_ot.id,datos)
            else:
                line = (0,get_ot.id,datos)
            lines.append(line)
        get_ot.materials_ids = lines

        lines = []
        for materi in self.rechazo_id:
            datos = {
                "decripcion":materi.decripcion,
                "fecha":materi.fecha,
                "hora":materi.hora,
                "firma":materi.firma
            }
            if self.env['dtm.proceso.rechazo'].search([("decripcion","=",materi.decripcion),("fecha","=",materi.fecha),
                                                         ("hora","=",materi.hora),("firma","=",materi.firma)]):
                line = (1,get_ot.id,datos)
            else:
                line = (0,get_ot.id,datos)
            lines.append(line)
        get_ot.rechazo_id = lines

        get_items = self.env['dtm.proceso.anexos'].search([("model_id","=",get_ot.id)])
        if not get_items:
            for archivo in self.anexos_id: # Inserta los archivos anexos jalandolos de ir_attachment y pasandolos al modelo de dtm.compras.facturado.archivos
                attachment = self.env['ir.attachment'].browse(archivo.id)
                datos = {
                    'documentos':attachment.datas,
                    'nombre': attachment.name,
                    'model_id': get_ot.id
                }
                get_items.create(datos)
        elif len(self.anexos_id) == len(get_items):
            for archivo in self.anexos_id: # Inserta los archivos anexos jalandolos de ir_attachment y pasandolos al modelo de dtm.compras.facturado.archivos
                attachment = self.env['ir.attachment'].browse(archivo.id)
                datos = {
                    'documentos':attachment.datas,
                    'nombre': attachment.name,
                    'model_id': get_ot.id
                }
                get_items.write(datos)

        elif len(self.anexos_id) != len(get_items):
            get_items.unlink()
            for archivo in self.anexos_id: # Inserta los archivos anexos jalandolos de ir_attachment y pasandolos al modelo de dtm.compras.facturado.archivos
                attachment = self.env['ir.attachment'].browse(archivo.id)
                datos = {
                    'documentos':attachment.datas,
                    'nombre': attachment.name,
                    'model_id': get_ot.id
                }
                get_items.create(datos)

        get_cortadora = self.env['dtm.proceso.cortadora'].search([("model_id","=",get_ot.id)])
        if not get_items:
            for archivo in self.cortadora_id: # Inserta los archivos anexos jalandolos de ir_attachment y pasandolos al modelo de dtm.compras.facturado.archivos
                datos = {
                    'documentos':archivo.documentos,
                    'nombre': archivo.nombre,
                    'model_id': get_ot.id
                }
                get_cortadora.create(datos)
        elif len(self.cortadora_id) == len(get_cortadora):
            for archivo in self.cortadora_id: # Inserta los archivos anexos jalandolos de ir_attachment y pasandolos al modelo de dtm.compras.facturado.archivos
                datos = {
                    'documentos':archivo.documentos,
                    'nombre': archivo.nombre,
                    'model_id': get_ot.id
                }
                get_cortadora.write(datos)

        elif len(self.cortadora_id) != len(get_cortadora):
            get_items.unlink()
            for archivo in self.cortadora_id: # Inserta los archivos anexos jalandolos de ir_attachment y pasandolos al modelo de dtm.compras.facturado.archivos
                datos = {
                    'documentos':archivo.documentos,
                    'nombre': archivo.nombre,
                    'model_id': get_ot.id
                }
                get_cortadora.create(datos)

        get_tubos = self.env['dtm.proceso.tubos'].search([("model_id","=",get_ot.id)])
        if not get_items:
            for archivo in self.tubos_id: # Inserta los archivos anexos jalandolos de ir_attachment y pasandolos al modelo de dtm.compras.facturado.archivos
                datos = {
                    'documentos':archivo.documentos,
                    'nombre': archivo.nombre,
                    'model_id': get_ot.id
                }
                get_tubos.create(datos)
        elif len(self.tubos_id) == len(get_tubos):
            for archivo in self.tubos_id: # Inserta los archivos anexos jalandolos de ir_attachment y pasandolos al modelo de dtm.compras.facturado.archivos
                datos = {
                    'documentos':archivo.documentos,
                    'nombre': archivo.nombre,
                    'model_id': get_ot.id
                }
                get_tubos.write(datos)

        elif len(self.tubos_id) != len(get_tubos):
            get_items.unlink()
            for archivo in self.tubos_id: # Inserta los archivos anexos jalandolos de ir_attachment y pasandolos al modelo de dtm.compras.facturado.archivos
                datos = {
                    'documentos':archivo.documentos,
                    'nombre': archivo.nombre,
                    'model_id': get_ot.id
                }
                get_tubos.create(datos)

    # -------------------------Acctions------------------------
    # def get_view(self, view_id=None, view_type='form', **options):
    #     res = super(NPI,self).get_view(view_id, view_type,**options)
    #     get_odt = self.env['dtm.materials.npi'].search([])
    #     for get in get_odt:
    #         get_this = self.env['dtm.diseno.almacen'].search([("nombre","=",get.nombre),("medida","=",get.medida)])
    #         if get_this:
    #             self.env.cr.execute("UPDATE dtm_materials_npi SET materials_list="+str(get_this.id)+" WHERE id="+str(get.id))
    #
    #     self.env.cr.execute("DELETE FROM dtm_materials_npi WHERE model_id is NULL")
    #     return res

    def action_autoNum(self): # Genera número consecutivo de NPI y OT

        get_npi = self.env['dtm.npi'].search_count([])

        # print(get_npi)
        if self.ot_number < get_npi:
            self.ot_number = get_npi

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


    @api.depends("materials_cuantity")
    def _compute_materials_inventory(self):
        for result in self:
            try:
                consulta  = self.consultaAlmacen()

                result.materials_required = 0
                cantidad = result.materials_cuantity
                inventario = consulta[0]
                print("npi",cantidad,inventario)
                if cantidad <= inventario:
                    result.materials_inventory = cantidad
                    # self.Apartado(result,cantidad)
                else:
                    result.materials_inventory = inventario
                    result.materials_required = cantidad - inventario

                requerido = result.materials_required
                if requerido > 0: # Manda comprar el material si este ya no hay en el almacén
                    get_odt = self.env['dtm.npi'].search([])
                    for get in get_odt:
                        for id in get.materials_ids:
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

    decripcion = fields.Text(string="Descripción del Rechazo")
    fecha = fields.Date(string="Fecha")
    hora = fields.Char(string="Hora")
    firma = fields.Char(string="Firma")

    @api.onchange("fecha")
    def _action_fecha(self):
        fecha = self.fecha

        if fecha:
            hora = fecha.strftime("%X")
            print(hora)
            self.hora = hora






        


