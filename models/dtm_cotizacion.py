from odoo import api,fields,models
from datetime import datetime



class DtmCotizacion(models.Model):
    _name = "dtm.cotizacion"
    
    po = fields.Char(string="PO")

    cliente_ids = fields.Many2one("res.partner",string="Empresa")

    atencion = fields.Char(string="Nombre del requisitor")

    no_cotizacion = fields.Char(string="No. De Cotización")

    date = fields.Date(string="Fecha" ,default= datetime.today())   

    attachment_ids = fields.Many2many("dtm.documentos.anexos",string="Anexos")

    telefono = fields.Char(string="Telefono")

    correo = fields.Char(string = "email")
    
    dibujos = fields.Boolean(string="Dibujos")

    fotos = fields.Boolean(string="Fotos")

    planos = fields.Boolean(string="Planos")

    npi = fields.Boolean(string="NPI")

    instalacion = fields.Boolean(string="Instalación")

    muestras_cliente = fields.Integer(string="Muesta(s) del Cliente")

    numero_muestras = fields.Integer(string="Número de Muestras")

    notes = fields.Text()

    #------------------------ Documentos Anexos------------------------
    list_materials_ids = fields.One2many('cot.list.material', 'model_id')


  
class ListMaterial(models.Model):
    _name = "cot.list.material"

    model_id = fields.Many2one("dtm.cotizacion")

    name = fields.Char(string="Nombre")
    descripcion = fields.Text(string="Descripción")
    cantidad = fields.Integer(string="Cantidad")
    precio = fields.Float(string = "Precio Unitario")
    total = fields.Float(string= "Total", compute="_compute_total")

    @api.depends("cantidad")
    def _compute_total(self):
        for record in self:
            record.total = record.precio * record.cantidad


    