# -*- coding: utf-8 -*-
{
    'name': "IET Attendance Api Integration",
    'summary': """
        This systems specify how to manage Attendance api integrations.
        """,

    'description': """
        This systems specify how to manage Attendance api integrations.
    """,

    'author': 'Mahmoud Salah',
    "version": "19.0.1.0.1",
    'category': 'Human Resources/Attendance',
    "license": "OPL-1",

    # any module necessary for this one to work correctly
    'depends': ['account', 'hr_attendance'],

    # always loaded
    'data': [
        "views/hr_attendance.xml",
        "data/ir_cron.xml"
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
    'installable': True,
    'application': True,
    "auto_install": False,
}
