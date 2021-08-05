# -*- encoding: utf-8 -*-

{
    'name' : 'Liquidaciones',
    'version' : '1.0',
    'category': 'Custom',
    'description': """Manejo de cajas chicas y liquidaciones""",
    'author': '',
    'website': '',
    'depends' : [ 'account' ],
    'data' : [
        'views/report.xml',
        'views/liquidacion_view.xml',
        'views/invoice_view.xml',
        'views/payment_view.xml',
        'views/reporte_liquidaciones.xml',
        'security/ir.model.access.csv',
        'security/liquidaciones_security.xml',
        'wizard/asignar_view.xml',
    ],
    'installable': True,
    'certificate': '',
}
