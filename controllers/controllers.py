from odoo import http
from odoo.http import request
import json

class WebSiteDirections(http.Controller):
    @http.route('/dtm_odt/get_data', type='http', auth='public', methods=['GET'])
    def get_compras(self, **kw):

        ntext_value = kw.get('ntext')
        print(ntext_value)
        materiales = request.env['dtm.materials.line'].sudo().search([('model_id','=',int(ntext_value))]).materials_list.mapped('id')
        print(materiales)
        # Construye la respuesta como un diccionario de Python
        result = [{'codigo': material} for material in materiales]
        # result = [{'codigo': ntext_value}]
        print(result)  # Para depuración en los logs

        # Convierte la respuesta a JSON y establece el encabezado de tipo de contenido
        return request.make_response(
            json.dumps(result),  # Convierte a una cadena JSON
            headers={'Content-Type': 'application/json'}
        )
