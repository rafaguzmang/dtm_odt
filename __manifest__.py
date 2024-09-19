{
    "name":"dtm_odt",
    "description":"Control ordenes de trabajo",
    # 'depends': ['base', 'mail','dtm_servicios_externos'],
    'depends': ['base', 'mail'],
    "data":[
        #Security
        'security/ir.model.access.csv',
        #Views
        'views/dtm_ot_view.xml',
        'views/dtm_npi_view.xml',
        #Menú
        'views/dtm_menu.xml',
        #Reports
        'reports/npi.xml',
        'reports/orden_de_trabajo.xml',
        'reports/rechazo.xml',
        'reports/lista_materiales.xml'
        ],
    'license': 'LGPL-3',
}
