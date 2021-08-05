# -*- coding: utf-8 -*-
{
    'name': "InFile FEL",
    'summary': """
        Generación de Factura Electrónica en Línea (FEL) de InFile
    """,
    'description': """
        Conexión a servicios de InFile para generación de Factura Electrónica en Línea (FEL)
    """,
    'author': "Mc-Sistemas",
    'website': "http://mcsistemas.net",
    'category': 'Sales',
    'sequence': 20,
    'version': '0.1',
    'depends': ['account','stock','point_of_sale'],
    'data': [
        'data/parameters.xml',
        "security/ir.model.access.csv",
        'views/infilefel_settings.xml',
        'views/account_tax.xml',
        'views/account_journal.xml',
        'views/account_invoice.xml',
    ],
    'installable': True,
    'auto_install': False,
}