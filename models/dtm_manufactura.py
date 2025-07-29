from odoo import models,fields,api
from datetime import datetime


class OrdenTrabajo(models.Model):
    _name = 'dtm.odt.manufactura'
    _description = 'Modulo para la manipulación de las ordenes desde el área de manufactura'

    od_number = fields.Integer(string="OD", readonly=True)
    ot_number = fields.Integer(string="OT", readonly=True)
    tipe_order = fields.Char(string="TIPO", readonly=True, default='NPI')
    revision_ot = fields.Integer(string="VERSIÓN", default=1, readonly=True)  # Esto es versión
    name_client = fields.Char(string="CLIENTE", default='Nombre del Cliente')
    product_name = fields.Char(string="NOMBRE DEL PRODUCTO", default='Nombre del Producto')
    date_in = fields.Date(string="ENTRADA", readonly=True)
    po_number = fields.Char(string="PO/Cot", readonly=True)
    date_rel = fields.Date(string="ENTREGA", readonly=True)