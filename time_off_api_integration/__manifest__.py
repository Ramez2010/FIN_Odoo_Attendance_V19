# -*- coding: utf-8 -*-
{
    'name': "Time Off Api Integration",
    'summary': """
        This systems specify how to manage time off api integrations.
        """,

    'description': """
        This systems specify how to manage time off api integrations.
    """,

    'author': 'Mahmoud Salah',
    'maintainer': 'Mahmoud Salah',
    'category': 'Human Resources/Time Off',
    # 'version': '17.0.1.0.0',
    "license": "OPL-1",

    # any module necessary for this one to work correctly
    'depends': ['hr_holidays', 'iet_api_access_token'],

    # always loaded
    'data': [
        "views/hr_leave.xml"
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
    'installable': True,
    'application': True,
    "auto_install": False,
}
