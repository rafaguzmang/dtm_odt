from odoo import fields,models

class Documentos(models.Model):
    _name = "dtm.documentos.anexos"

    documentos = fields.Binary(string="Documentos")
    nombre = fields.Char()