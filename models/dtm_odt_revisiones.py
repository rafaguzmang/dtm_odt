from odoo import api,models,fields
from datetime import datetime


class Revisiones(models.Model):
    _name = 'dtm.odt.revisiones'
    _description = 'Modelo para guardar reviciones'
    _order = 'ot_number desc'
    _rec_name = 'ot_number'

    ot_number = fields.Integer(string="OT", readonly=True)
    tipe_order = fields.Char(string=" ", readonly=True, default='NPI')
    name_client = fields.Char(string="CLIENTE", readonly=True)
    product_name = fields.Char(string="NOMBRE DEL PRODUCTO", readonly=True)
    date_in = fields.Date(string="ENTRADA",  readonly=True)
    po_number = fields.Char(string="PO/Cot", readonly=True)
    date_rel = fields.Date(string="ENTREGA", readonly=True)
    version_ot = fields.Integer(string="VERSIÓN OT",  readonly=True)
    color = fields.Char(string="COLOR", default="N/A", readonly=True)
    cuantity = fields.Integer(string="CANTIDAD", readonly=True)
    disenador = fields.Char("Diseñador", readonly=True)
    firma = fields.Char(string="Firma", readonly=True)
    firma_ventas = fields.Char(string="Aprobado", readonly=True)
    firma_ingenieria = fields.Char(string="Nesteo", readonly=True)
    po_fecha = fields.Date(string="Fecha PO", readonly=True)
    planos = fields.Boolean(string="Planos", default=False)
    nesteos = fields.Boolean(string="Nesteos", default=False)
    status = fields.Char(string="Status", readonly=True)

    date_disign_finish = fields.Date(string="Fecha Diseño", readonly=True)
    costo_material = fields.Float(string="Costo", readonly=True)

    description = fields.Text(string="DESCRIPCIÓN", readonly=True)

    # ------------------------Notas---------------------------
    notes = fields.Text(string="Notas", readonly=True)

    #----------------Foreing tables---------------------------

    ligas_id = fields.Many2many("dtm.odt.ligas",readonly=True)

    orden_compra_pdf = fields.Many2many("ir.attachment", string='File', readonly=True)
    #
    # # Lista de materiales
    # materials_ids = fields.Many2many("dtm.materials.line", string="Lista", readonly=True)
    # # Archivos mandados por ventas
    anexos_ventas_id = fields.Many2many("ir.attachment", "anexos_ventas_id2", string="Archivos", readonly=True)
    anexos_id = fields.Many2many("ir.attachment",'anexos_id2', string="Archivos", readonly=True)
    cortadora_id = fields.Many2many("ir.attachment", "cortadora_id2", string="Segundas piezas", readonly=True)
    tubos_id = fields.Many2many("ir.attachment", "tubos_id2", readonly=True)
    # # Planos
    archivos_id = fields.Many2many('dtm.documentos.anexos', readonly=True)
    # maquinados_id = fields.One2many("dtm.odt.servicios", "extern_id")
    primera_pieza_id = fields.Many2many("ir.attachment", "primera_pieza_id2", string="Primeras piezas", readonly=True)
    ligas_tubos_id = fields.Many2many("dtm.odt.ligas", "model_tubo_id", readonly=True)

    def action_pasive(self):
        pass
