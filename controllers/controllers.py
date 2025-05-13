from datetime import datetime
from odoo import http
from odoo.http import request,Response
import json

class WebSiteDirections(http.Controller):
    @http.route('/dtm_odt/get_data', type='http', auth='public', methods=['GET'])
    def get_compras(self, **kw):

        ntext_value = kw.get('ntext')
        materiales = request.env['dtm.materials.line'].sudo().search([('model_id','=',int(ntext_value)),('comprado','=',True)]).materials_list.mapped('id')
        # Construye la respuesta como un diccionario de Python
        result = [{'codigo': material} for material in materiales]
        # result = [{'codigo': ntext_value}]

        # Convierte la respuesta a JSON y establece el encabezado de tipo de contenido
        return request.make_response(
            json.dumps(result),  # Convierte a una cadena JSON
            headers={'Content-Type': 'application/json',
                      'Access-Control-Allow-Origin': '* ',
                     }
        )

    @http.route('/diseno_indicadores', type='json', auth='public')
    def get_compras(self, **kw):

        indicadores = []
        for month in range(1, 13):
            if month <= int(datetime.today().strftime("%m")):
                request.env.cr.execute(
                    " SELECT ot_number,create_date,version_ot FROM dtm_facturado_odt WHERE EXTRACT(MONTH FROM create_date) = " + str(
                        month) +
                    " AND EXTRACT(YEAR FROM create_date) = " + datetime.today().strftime("%Y") + ";")
                get_query = request.env.cr.fetchall()
                if get_query:
                    ordenes = len(get_query)
                    versiones = len(list(filter(lambda x:x[2]>=3,get_query)))
                    porciento = round((((ordenes - versiones) * 100) / ordenes), 2)
                    mes = str(get_query[0][1].strftime("%B")).capitalize() if len(get_query[0][1].strftime("%B")) > 0 else datetime.today().strftime("%B").capitalize()
                    indicadores.append({'totales': ordenes, 'versiones': versiones, 'porciento': porciento, 'mes': mes})

        return indicadores
