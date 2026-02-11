# -*- coding: utf-8 -*-
{
    'name': "fixing",
    'summary': """fixing""",
    'description': """fixing""",
    'author': "H",
    'version': '0.1',
    'depends': ['base', 'account', 'account_reports', 'analytic', 'web'],
    'license': 'LGPL-3',
    'data': [
        'views/account_report_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'iet_fixing_report/static/src/xml/account_report_filters.xml',
            'iet_fixing_report/static/src/js/account_report_filters_patch.js',
        ],
    },
}
