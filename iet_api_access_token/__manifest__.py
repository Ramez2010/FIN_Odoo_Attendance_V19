# -*- coding: utf-8 -*-
{
    'name': "IET API Access Token",
    'summary': """
        This systems specify how to manage User Access Token.
        """,

    'description': """
        This systems specify how to manage User Access Token.
    """,

    'author': 'Mahmoud Salah',
    'maintainer': 'Mahmoud Salah',
    'category': 'Base',
    "license": "OPL-1",

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        "views/res_users.xml",
        "data/ir_cron.xml"
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
    'installable': True,
    'application': True,
    "auto_install": False,
}
