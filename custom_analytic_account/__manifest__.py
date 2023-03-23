# -*- coding: utf-8 -*-
{
    'name':
    "Analytic Account Customization",
    'summary':
    """  display customer related analytic account 
        """,
    'author':
    "Code Flex",
    'website':
    "http://www.yourcompany.com",

    'category':
    'Uncategorized',
    'version':
    '0.1',
    'license':
    'LGPL-3',
    # any module necessary for this one to work correctly
    'depends': [
        'sale_management',
        'account_accountant',
        'stock',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_payment.xml',
        'views/stock_picking.xml',
        'views/account_move.xml',
        'wizards/account_payment_register_views.xml',
    ],
}
