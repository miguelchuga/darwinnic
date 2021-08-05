# -*- coding: utf-8 -*-
{
    'name': "edx FEL",
    'summary': """
        Generación de Factura Electrónica en Línea (FEL) de EDX
    """,
    'description': """
        Conexión a servicios de EDX para generación de Factura Electrónica en Línea (FEL)
    """,
    'author': "Mc-Sistemas",
    'website': "http://mcsistemas.net",
    'category': 'Sales',
    'sequence': 20,
    'version': '0.1',
    'depends': ['base','account'],
    'data': [
        'data/parameters.xml',
#        "security/ir.model.access.csv",
#        'views/edxfel_settings.xml',
        'views/account_tax.xml',
        'views/account_journal.xml',
        'views/account_invoice.xml',
    ],
    'installable': False,
    'auto_install': False,
}
