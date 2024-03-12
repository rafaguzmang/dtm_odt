from odoo import fields,models

class Documentos(models.Model):
    _name = "dtm.documentos.anexos"

    documentos = fields.Binary(string="Documentos", attachement=True, readonly=False)
    nombre = fields.Char()