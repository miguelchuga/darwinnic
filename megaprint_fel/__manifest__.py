# -*- coding: utf-8 -*-
{
    'name': "Megaprint FEL",
    'summary': """
        Generación de Factura Electrónica en Línea (FEL) de Megaprint
    """,
    'description': """
        Conexión a servicios de Megaprint para generación de Factura Electrónica en Línea (FEL)
    """,
    'author': "Mc-sistemas",
    'website': "",
    'category': 'Sales',
    'sequence': 20,
    'version': '0.1',
    'depends': ['base_setup','account','stock','point_of_sale'],
    'data': [
        "data/parameters.xml",
#        "security/ir.model.access.csv",
        'views/mpfel_settings.xml',
        'views/account_tax.xml',
        'views/account_journal.xml',
        'views/account_invoice.xml',
    ],
    'installable': True,
    'auto_install': False,
}
