# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd. (<http://www.devintellecs.com>).
#
##############################################################################
{
    'name': 'Conciliación Bancaria',
    'version': '1.0',
    'sequence':1,
    'description': """
        Conciliación bancaria adaptado a Guatemala.
    """,
    "category":'Account',
    'summary': 'Conciliación del estado de cuenta bancario.',
    'author': 'Mc-Sistemas',
    'website': 'http://mcsistemas.net',
    'depends': ['base',
                #'report',
                'account',
                'report_xlsx'],
    'data': [
            'security/ir.model.access.csv',
            'report/report_menu.xml',
            'views/bank_reconciliation_view.xml',
            'report_menu.xml',
            'views/report_bank_reconcile.xml',
            'views/account_view.xml'
            ],
    'demo': [],
    'test':[],
    'application':True,
    'installable': True,
    'auto_install': False,
    'price':00.01,
    'currency':'QTZ'
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: