{
    "name":"dtm_odt",
    "description":"Control ordenes de trabajo",
    "data":[
        #Security
        'security/ir.model.access.csv',
        #Views
        'views/dtm_odt_view.xml',
        'views/dtm_ing_view.xml',
        'views/dtm_npi_view.xml',

        #Reports
        'reports/npi.xml',
        'reports/orden_de_trabajo.xml',
        'reports/rechazo.xml',
        'reports/lista_materiales.xml'


        ],
    "depends" : ["base"]
     
}
