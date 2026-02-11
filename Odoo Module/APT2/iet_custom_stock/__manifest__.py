# -*- coding: utf-8 -*-
{
    'name': "iet_custom_stock",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,
    'license': 'LGPL-3',
    'author': "My Company",
    'website': "https://www.yourcompany.com",

    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'arabic_product_name'],

    # always loaded
    'data': [
        'views/stock_lot.xml',
        'views/stock_quan.xml',
        'views/stock_move.xml',
        'report/print_label_inherit.xml',
    ],

}
