from odoo import fields,models

class Documentos(models.Model):
    _name = "dtm.documentos.anexos"
    _description = "Guarda todos los planos de la orden de trabajo"

<<<<<<< HEAD
    documentos = fields.Binary()
    nombre = fields.Char()


class Cortadora(models.Model):
    _name = "dtm.documentos.cortadora"
    _description = "Guarda los nesteos del Radán"

    documentos = fields.Binary()
    nombre = fields.Char()

class Tubos(models.Model):
    _name = "dtm.documentos.tubos"
    _description = "Guarda los nesteos de la cortadora de tubos"

    documentos = fields.Binary()
    nombre = fields.Char()
=======
    documentos = fields.Binary(string="Documentos", attachement=True, readonly=False)
    nombre = fields.Char()
>>>>>>> 94d2de79a5d1a0041ba0b706c6312970371f18b9
