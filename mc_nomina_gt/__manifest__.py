# -*- coding: utf-8 -*-
{
    'name': "mc_nomina_gt",

    'summary': """
        - Planillas
        - Recibos de pago
        - Libro de Salarios
        - Bono 14
        - Aguinaldo
        - Vacaciones
        - Igss
        - Informe anual de empleador
        - Planilla del Igss
        - Provisiones de nomina""",

    'description': """
        Nomina para Guatemala
    """,
    'author': "Mc-Sistemas / Miguel Chuga",

    'website': "http:mcsistemas.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Custo',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr', 'hr_payroll_account','hr_contract'],
    #,'account_analytic_analysis'

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/hr_view.xml',
        'views/catalogos_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_salary_rule_view.xml',
#        'views/hr_payroll_analytic_account_view.xml',
        'views/report_recibos.xml',
        'views/hr_payroll_report.xml',
        'views/hr_x_reglas_dias.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}