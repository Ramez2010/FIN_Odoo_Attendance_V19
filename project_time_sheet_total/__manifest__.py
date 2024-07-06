# -*- coding: utf-8 -*-
{
    'name': "Project Time Sheet total",
    'summary': "timesheet total",
    'description': """""",
    'author': "abd-elhamed saad",
    'website': "https://www.linkedin.com/in/abd-el-hamed-saad/",
    'category': 'Services',
    'version': '16.0.1',
    'license': "AGPL-3",
    'depends': ['base', 'project', 'account', 'hr_timesheet', 'hr', 'hr_payroll_account', 'account_asset'],
    'data': [
        'views/views.xml',
        'views/hr._contract.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
