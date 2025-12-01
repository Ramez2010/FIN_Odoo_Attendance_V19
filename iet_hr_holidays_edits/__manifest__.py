# -*- coding: utf-8 -*-
{
    'name': "IET HR Holidays Edits",

    'summary': """
        Custom Employee Leave
        """,

    'description': """
        Edit Employee Leave Approvals
    """,

    'author': "Mohammed Abd Elkhalek",
    'website': "https://www.intelligent-experts.com",

    'category': 'Human Resources/Time Off',
    'version': '19.0.0.0',

    "license": "AGPL-3",
    'depends': ['base', 'hr_holidays'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ],

}
