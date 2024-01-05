from odoo import api,models,fields

class DtmOdt(models.Model):
    _name = "dtm.ing"


    name = fields.Char(string="Nombre", required=True)
    color = fields.Integer()
