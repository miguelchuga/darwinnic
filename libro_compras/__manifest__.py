# -*- coding: utf-8 -*-
{
    'name': "Libro Compras Excel V13",

    'summary': """
        Reporte de Libro Compras en Excel para V13
        """,

    'description': """
        Reporte de Libro Compras en Excel para V13
    """,

    'author': "Erik Yol",
    'website': "https://mcsistemas.odoo.com/",

    'category': 'Reports',
    'version': '0.1',

    'depends': ['base','report_xlsx'],

    'data': [
        # 'security/ir.model.access.csv',
        #'views/views.xml',
        #'views/templates.xml',
        'views/report_menu.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable':True
}
