from odoo import http
from odoo.http import request
import json


class WebSiteDirecctions(http.Controller):
    @http.route('/direccion',  auth="public", website="True")
    def get_compras(self, **kw):
        materiales = http.request.env['dtm.compras.realizado'].sudo().search([])
        result = [{'id':material.id} for material in materiales]
        print(result)
        return json.dumps(result)
