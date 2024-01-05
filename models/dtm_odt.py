from odoo import api,models,fields
from datetime import datetime
import re



class DtmOdt(models.Model):
    _name = "dtm.odt"
    _description = "Oden de trabajo"
    _order = "ot_number desc"

   
    #---------------------Basicos----------------------

    status = fields.Many2many("dtm.ing" ,string="Estado del Producto")

    sequence = fields.Integer()
    ot_number = fields.Char("NÚMERO",default="000",readonly=False)
    tipe_order = fields.Selection([("npi","NPI"),("ot","OT")],"TIPO",required=True)
    # name_client = fields.Many2one("res.partner",string="CLIENTE")
    name_client = fields.Char(string="CLIENTE")
    
    product_name = fields.Char(string="NOMBRE DEL PRODUCTO")
   
    date_in = fields.Date(string="FECHA DE ENTRADA", default= datetime.today())
    
    po_number = fields.Char(string="PO",default="00")
    date_rel = fields.Date(string="FECHA DE ENTREGA", default= datetime.today())

    version_ot = fields.Integer(string="VERSIÓN OT",default=1,readonly=True)
    color = fields.Char(string="COLOR",default="N/A")
    cuantity = fields.Integer(string="CANTIDAD" , default=1)

    materials_ids = fields.One2many("dtm.materials.line","model_id",string="Lista")

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
        

    #-----------------------Materiales----------------------

    class TestModelLine(models.Model):
     
        _name = "dtm.materials.line"
        _description = "Tabla de materiales"

        model_id = fields.Many2one("dtm.odt", readonly=True)
       
        materials_list = fields.Char("LISTADO DE MATERIALES")
        materials_cuantity = fields.Char("CANTIDAD", default=1)
        materials_inventory = fields.Char("INVENTARIO")
        materials_required = fields.Char("REQUERIDO", default=0)

        


