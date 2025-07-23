# -*- coding: utf-8 -*-
{
    'name': "IET Analytic Account Edits",

    'summary': """
        Analytic Account Edits""",

    'description': """
        -Adding Analytic Account ID Sequence Instead Of Reference.
    """,

    'author': "Mohammed Abd Elkhalek",
    'website': "https://www.intelligent-experts.com",


    'category': 'Accounting/Accounting',
    'version': '16.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'analytic', 'stock', 'custom_analytic_account', 'analytic_account_in_stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/analytic_account_sequence.xml',
        'views/stock_picking_inherit.xml',
        'views/analytic_account.xml',
    ],

}
