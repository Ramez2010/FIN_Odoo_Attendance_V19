# -*- coding: utf-8 -*-
{
    'name': "apte_sales_report",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Tareq Aljezawi | IET",
    'version': '1.0',
    'depends': ['base', 'sale'],

    # always loaded
    'data': [
        # 'security/security.xml',
        'views/pivot_view.xml',
    ],
    "license": "LGPL-3",
    "installable": True,

}
