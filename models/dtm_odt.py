from odoo import api,models,fields
from datetime import datetime
from odoo.exceptions import ValidationError
import re



class DtmOdt(models.Model):
    _name = "dtm.odt"
    _description = "Oden de trabajo"
    _order = "ot_number desc"
   
    #---------------------Basicos----------------------

    status = fields.Many2many("dtm.ing" ,string="Estado del Producto")
    sequence = fields.Integer()
    ot_number = fields.Char("NÚMERO",default="000",readonly=True)
    tipe_order = fields.Selection([("npi","NPI"),("ot","OT")],"TIPO",required=True,readonly=True)
    name_client = fields.Char(string="CLIENTE",readonly=True)
    product_name = fields.Char(string="NOMBRE DEL PRODUCTO",readonly=True)
    date_in = fields.Date(string="FECHA DE ENTRADA", default= datetime.today(),readonly=True)
    po_number = fields.Char(string="PO",default="00",readonly=True)
    date_rel = fields.Date(string="FECHA DE ENTREGA", default= datetime.today())
    version_ot = fields.Integer(string="VERSIÓN OT",default=1,readonly=True)
    color = fields.Char(string="COLOR",default="N/A")
    cuantity = fields.Integer(string="CANTIDAD",readonly=True)
    materials_ids = fields.One2many("dtm.materials.line","model_id",string="Lista")

    planos = fields.Boolean(string="Planos",default=False)
    nesteos = fields.Boolean(string="Nesteos",default=False)

    rechazo_id = fields.One2many("dtm.odt.rechazo", "model_id")

    anexos_id = fields.Many2many("dtm.documentos.anexos")


    #---------------------Resumen de descripción------------

    description = fields.Text(string= "DESCRIPCIÓN",placeholder="RESUMEN DE DESCRIPCIÓN")

    #------------------------Notas---------------------------

    notes = fields.Text()

    #-------------------------Acctions------------------------
    def action_autoNum(self): # Genera número consecutivo de NPI y OT
        res=[]
        newres = []
        self.env.cr.execute("SELECT ot_number from dtm_odt ")
        result = self.env.cr.fetchall() 

        for n in result:
            res.append(n[0])

        if self.tipe_order =="ot":   
            regex = re.compile("[0-9]+$")
            for n in res:
                if regex.match(n):
                    newres.append(int(n))
            newres.sort(reverse=True)
            self.ot_number = newres[0]  + 1

        elif  self.tipe_order =="npi": 
            regex = re.compile(".*-NPI$")
            for n in res:
                if regex.match(n):
                    newres.append(int(n.replace("-NPI","")))
            newres.sort(reverse=True)
            self.ot_number = str(newres[0]  + 1)+ "-NPI"


    def action_imprimir_formato(self): # Imprime según el formato que se esté llenando
        if self.tipe_order == "npi":
            return self.env.ref("dtm_odt.formato_npi").report_action(self)
        elif self.tipe_order == "ot":
            return self.env.ref("dtm_odt.formato_orden_de_trabajo").report_action(self)
            # return self.env.ref("dtm_odt.formato_rechazo").report_action(self)

    def action_imprimir_materiales(self): # Imprime según el formato que se esté llenando
            return self.env.ref("dtm_odt.formato_lista_materiales").report_action(self)



    #-----------------------Materiales----------------------

class TestModelLine(models.Model):
    _name = "dtm.materials.line"
    _description = "Tabla de materiales"

    model_id = fields.Many2one("dtm.odt")

    materials_list = fields.Many2one("dtm.diseno.almacen", string="LISTADO DE MATERIALES")
    materials_cuantity = fields.Integer("CANTIDAD")
    materials_inventory = fields.Integer("INVENTARIO", compute="_compute_materials_inventory", store=True)
    materials_required = fields.Integer("REQUERIDO")

    @api.depends("materials_cuantity")
    def _compute_materials_inventory(self):
        for result in self:
            cantidad = result.materials_cuantity
            inventario = result.materials_list.cantidad
            # print(cantidad,inventario)
            if cantidad <= inventario:
                result.materials_inventory = cantidad
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
                descripcion = result.materials_list.caracteristicas
                if not descripcion:
                    descripcion = ""
                self.env.cr.execute("INSERT INTO dtm_compras_requerido(orden_trabajo,nombre,cantidad,description) VALUES('"+orden+"', '"+nombre+"', "+str(requerido)+", '"+descripcion+"')")


    @api.onchange("materials_list")
    def _onchange_material_list(self):
        print(self._origin.id)
        print(self.materials_list.nombre)

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
            print(hora)
            self.hora = hora






        


