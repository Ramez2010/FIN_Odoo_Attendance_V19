# -*- coding: utf-8 -*-
{
    'name': "IET Employee Hourly Rate",

    'summary': """
        Employee Hourly Rate""",

    'description': """
        Employee Hourly Rate
    """,

    'author': "Mohammed Abd Elkhalek",
    'website': "https://www.intelligent-experts.com",


    'category': 'Human Resources/Employees',
    'version': '16.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_contract'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/employee_hourly_rate_views.xml',
        'views/hr_contract_views.xml',
    ],

}
