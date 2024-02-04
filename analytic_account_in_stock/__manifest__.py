# -*- coding: utf-8 -*-
{
    'name': "analytic_account_in_stock",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Mohamed0halim",
    'website': "linkedin.com/in/mo-halim",
    'version': '0.1',

    'depends': ['base', 'stock', 'account_asset'],
    # always loaded
    'data': [
        'security/security.xml',
        'views/views.xml',
        'views/operation_type.xml',
    ],

}
