from odoo import http
from odoo.http import request
import json

class NesteoController(http.Controller):
    @http.route('/dtm_odt/get_nesteo_data', type='http', auth='public', csrf=False)
    def get_nesteo_data(self, **kw):

        get_nesteo = request.env['dtm.odt'].sudo().search([('nesteo_chk','=',True),('manufactura','=',False)])
        result = []
        for item in get_nesteo:
            result.append({
                'id': item.id,
                'ot_number': item.ot_number,
                'version_ot': item.version_ot,
                'tipo_orden': item.tipe_order,
                'cliente': item.name_client,
                'producto': item.product_name,
                'cantidad': item.cuantity,
                'disenador': item.disenador,
                'fecha_llegada':item.nesteo_inicio.strftime('%Y-%m-%d'),
            })
        
       
        return request.make_response(
            json.dumps(result),
            headers={
                "Content-Type":"application/json",
                "Access-Control-Allow-Origin":"*"
            }
        )
