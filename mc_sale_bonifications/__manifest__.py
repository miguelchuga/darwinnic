# -*- coding: utf-8 -*-
{
    'name': "Sale bonifications",
    'summary': """
        Bonifications in sales by product / Mc-Sistemas
    """,
    'description': """
        Bonification scheme in sales.
        
        Each product can have a bonification depending in the quantity purchased.   The bonification can be the same or other product,
        and the quantity of that bonification can be set depending on different quantity ranges.
    """,
    'author': "",
    'website': "",
    'category': 'sale',
    'sequence': 20,
    'version': '0.1',
    'depends': ['sale'],
    'data': [
        'views/product_template.xml',
        'views/sale_order.xml',
    ],
    'installable': True,
    'auto_install': False,
}
