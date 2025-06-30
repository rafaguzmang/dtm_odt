from odoo import fields,models



class Tubos(models.Model):
    _name = "dtm.documentos.tubos"
    _description = "Guarda los nesteos de la cortadora de tubos"

    documentos = fields.Binary()
    nombre = fields.Char()
