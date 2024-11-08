from odoo import http
from odoo.http import request

class WebSiteDirections(http.Controller):
    @http.route('/dtm_odt/get_data', type='json', auth='public', website=True)
    def get_compras(self, **kw):
        materiales = request.env['dtm.compras.realizado'].sudo().search([])
        result = [{'id': material.id} for material in materiales]
        print(result)
        return result
