from email.policy import default

from odoo import fields, models, api


class Retrabajo(models.Model):
    _name = 'dtm.odt.retrabajo'
    _description = 'Modelo para llevar la bitácora de los retrabajos'

    model_id = fields.Many2one('dtm.odt')

    name = fields.Selection(string='Diseñador', selection=[('andres','Andrés Alberto Orozco Martínez'),('luis','Luis Donaldo García Rayos'),('bryan','Bryan Alejandro Banda Moreno')])
    motivo = fields.Text(string="Motivo")
    version = fields.Integer(string='Versión', readonly=True, related='model_id.revision_ot',)
    revision = fields.Integer(string='Revisión', readonly=True, related='model_id.version_ot',)
