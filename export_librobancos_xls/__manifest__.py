{
    'name': 'Exporta Libro de Bancos a MS Excel',
    'version': '0.2',
    'category': 'Report',
    'license': "AGPL-3",
    'summary': "Exporta Libro de Bancos a MS Excel.",
    'author': 'Miguel Chuga',
    'company': 'MC Sistemas',
    'website': 'http://www.mcsistemas.net',
    'depends': [
                'base',
                'stock',
                'sale',
                'purchase',
                'report_xlsx'
                ],
    'data': [
            'views/wizard_view.xml',
            ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
}
