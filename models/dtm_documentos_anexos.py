from odoo import fields,models

class Documentos(models.Model):
    _name = "dtm.documentos.anexos"
    _description = "Guarda todos los planos de la orden de trabajo"
    documentos = fields.Binary()
    nombre = fields.Char()






class Tubos(models.Model):
    _name = "dtm.documentos.tubos"
    _description = "Guarda los nesteos de la cortadora de tubos"

    documentos = fields.Binary()
    nombre = fields.Char()
