from odoo import api,models,fields
from datetime import datetime
from odoo.exceptions import ValidationError
from fractions import Fraction
import re

class DtmOdt(models.Model):
    _name = "dtm.odt"
    _description = "Oden de trabajo"
    # _order = "ot_number desc"

    #---------------------Basicos----------------------

    status = fields.Char(readonly=True)
    ot_number = fields.Char(string="NÚMERO",readonly=True)
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

    planos = fields.Boolean(string="Planos",default=False)
    nesteos = fields.Boolean(string="Nesteos",default=False)

    rechazo_id = fields.One2many("dtm.odt.rechazo", "model_id")
    anexos_id = fields.Many2many("ir.attachment")
    cortadora_id = fields.Many2many("dtm.documentos.cortadora")
    tubos_id = fields.Many2many("dtm.documentos.tubos")

    #---------------------Resumen de descripción------------

    description = fields.Text(string="DESCRIPCIÓN")

    #------------------------Notas---------------------------

    notes = fields.Text(string="notes")

    #-------------------------Acctions------------------------
    # def get_view(self, view_id=None, view_type='form', **options):
    #     res = super(DtmOdt,self).get_view(view_id, view_type,**options)
    #
    #     get_self = self.env['dtm.odt'].search([])
    #     print(len(get_self))
    #     for num in range(1,len(get_self)+1):
    #         print(num)
    #         get_po = self.env['dtm.compras.items'].search([('orden_trabajo','=',num)])
    #         if get_po:
    #             # print(get_po[0].id,get_po[0].model_id.id,get_po[0].orden_trabajo)
    #             get_data = self.env['dtm.ordenes.compra'].search([("id","=",get_po[0].model_id.id)])
    #             # print(get_data.orden_compra,get_data.cliente_prov)
    #             vals = {
    #                 'ot_number':get_po[0].orden_trabajo,
    #                 'tipe_order':"OT",
    #                 'name_client':get_data.cliente_prov,
    #                 'product_name':get_po[0].item,
#                     'product_name': get_po[0].cantidad,
    #                 'po_number':get_data.orden_compra,
    #             }
    #             print(vals)
    #             self.env['dtm.odt'].search([('ot_number','=',get_po[0].orden_trabajo)]).write(vals)
    #
    #     # get_odt = self.env['dtm.materials.line'].search([])
    #     # for get in get_odt:
    #     #     get_this = self.env['dtm.diseno.almacen'].search([("nombre","=",get.nombre),("medida","=",get.medida)])
    #     #     if get_this:
    #     #         self.env.cr.execute("UPDATE dtm_materials_line SET materials_list="+str(get_this.id)+" WHERE id="+str(get.id))
    #     #
    #     # self.env.cr.execute("DELETE FROM dtm_materials_line WHERE model_id is NULL")
    #
    #     return res


    def action_imprimir_formato(self): # Imprime según el formato que se esté llenando
        if self.tipe_order == "NPI":
            return self.env.ref("dtm_odt.formato_npi").report_action(self)
        elif self.tipe_order == "OT":
            return self.env.ref("dtm_odt.formato_orden_de_trabajo").report_action(self)
            # return self.env.ref("dtm_odt.formato_rechazo").report_action(self)

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

    def consultaAlmacen(self):

        nombre = str(self.nombre)
        medida = self.medida
        # print(nombre)
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

        # print("Result",materiales.cantidad,sum,materiales,get_almacen)
        return (cantidad_materiales - sum,materiales,get_almacen,sum)

    @api.depends("materials_cuantity")
    def _compute_materials_inventory(self):
        for result in self:
            # try:
                consulta  = self.consultaAlmacen()

                result.materials_required = 0
                cantidad = result.materials_cuantity
                inventario = consulta[0]
                # print(cantidad,inventario)
                if cantidad <= inventario:
                    result.materials_inventory = cantidad
                    # self.Apartado(result,cantidad)
                else:
                    result.materials_inventory = inventario
                    result.materials_required = cantidad - inventario
                requerido = result.materials_required
                if requerido > 0:
                    get_odt = self.env['dtm.odt'].search([])
                    for get in get_odt:
                        for id in get.materials_ids:
                            if result._origin.id == id.id:
                                orden = get.ot_number

                    nombre = result.materials_list.nombre
                    if result.materials_list.medida:
                        nombre = result.materials_list.nombre +" " + result.materials_list.medida

                    descripcion = ""
                    if descripcion:
                        descripcion = result.materials_list.caracteristicas

                    get_requerido = self.env['dtm.compras.requerido'].search([("orden_trabajo","=",orden),("nombre","=",nombre)])

                    if not get_requerido:
                        self.env.cr.execute("INSERT INTO dtm_compras_requerido(orden_trabajo,nombre,cantidad) VALUES('"+orden+"', '"+nombre+"', "+str(requerido)+")")
                    else:
                        self.env.cr.execute("UPDATE dtm_compras_requerido SET cantidad="+ str(requerido)+" WHERE orden_trabajo='"+orden+"' and nombre='"+nombre+"'")
                    if requerido <= 0:
                        self.env.cr.execute("DELETE FROM dtm_compras_requerido WHERE cantidad = 0")

                if cantidad <= 0:
                    result.materials_cuantity = 0
                    result.materials_inventory = 0
                    result.materials_required = 0

                if inventario < 0:
                    result.materials_inventory = 0

                disponible = 0
                if consulta[1]:
                    disponible = consulta[1].cantidad - (consulta[3] + cantidad)

                if disponible < 0:
                    disponible = 0

                vals = {
                    "apartado": consulta[3]+cantidad,
                    "disponible": disponible
                }
                if consulta[1]:
                    # print("error",consulta[1],disponible,consulta[3]+cantidad)
                    consulta[1].write(vals)
                vals = {
                    "cantidad": disponible
                }
                consulta[2].write(vals)
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

    decripcion = fields.Text(string="Descripción del Rechazo")
    fecha = fields.Date(string="Fecha")
    hora = fields.Char(string="Hora")
    firma = fields.Char(string="Firma")

    @api.onchange("fecha")
    def _action_fecha(self):
        fecha = self.fecha

        if fecha:
            hora = fecha.strftime("%X")
            # print(hora)
            self.hora = hora









