from datetime import datetime
from odoo import http
from odoo.http import request,Response
import json,requests
import datetime


class WebSiteDirections(http.Controller):
    @http.route('/dtm_odt/get_data', type='http', auth='public',  csrf=False)
    def get_compras(self, **kw):

        ntext_value = kw.get('ntext')
        materiales = request.env['dtm.materials.line'].sudo().search([('model_id','=',int(ntext_value)),('comprado','=',True)]).materials_list.mapped('id')
        # Construye la respuesta como un diccionario de Python
        result = [{'codigo': material} for material in materiales]


        return request.make_response(
            json.dumps(result),
            headers={
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
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


    @http.route('/dtm_diseno', type='http', auth='public',  csrf=False)
    def get_diseno(self):

        precio_dolar_json = self.precioDollar()
        precio_dolar = float(precio_dolar_json['bmx']['series'][0]['datos'][0]['dato'])

        get_diseno = request.env['dtm.odt'].sudo().search([('ot_number','=',0)])
        result = []
        for material in get_diseno:
            get_cotizacion = request.env['dtm.compras.items'].sudo().search([('orden_diseno','=',material.od_number)],limit=1).model_id.no_cotizacion_id.precotizacion
            get_cotizacion = request.env['dtm.cotizaciones'].sudo().search([('no_cotizacion','=',get_cotizacion)],limit=1).curency
            dolar = precio_dolar if get_cotizacion == 'us' else 1
            result.append({
                'id': material.id,
                'orden_diseno': material.od_number,
                'tipo_orden': material.tipe_order,
                'version': material.version_ot,
                'cliente': material.name_client,
                'producto': material.product_name,
                'cantidad': material.cuantity,
                'po_number': material.po_number,
                'po_file': request.env['dtm.compras.items'].sudo().search([('orden_diseno','=',material.od_number)],limit=1).model_id.archivos_id[0].datas.decode('utf-8') if request.env['dtm.compras.items'].sudo().search([('orden_diseno','=',material.od_number)],limit=1).model_id.archivos_id.datas else '',
                'precio': round((request.env['dtm.compras.items'].sudo().search([('orden_diseno','=',material.od_number)],limit=1).mapped('precio_total')[0])*dolar,2),
                'disenador': material.disenador,
                'fecha_llegada':material.create_date.strftime('%Y-%m-%d') if material.create_date else '--/--/----',
                'fecha_termino_diseno':material.date_disign_finish.strftime('%Y-%m-%d') if material.date_disign_finish else '--/--/----',
                'fecha_entrega_cliente': material.date_rel.strftime('%Y-%m-%d') if material.date_rel else '--/--/----',
            })
        return request.make_response(
            json.dumps(result),
                headers={
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                }
            )

    def precioDollar(self):
        try:
            result = requests.get("https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF60653/datos/oportuno?token=48ae5fcf525e8658eb784d0c4030054d7aa97bf2b5859747015820245978f739",timeout=5)
            result.raise_for_status()
            return result.json()
        except  Exception as e:
            return {"error": str(e)}
