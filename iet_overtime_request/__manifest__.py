{
    'name': "iet_overtime_request",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,
    'author': "Tareq Aljezawi | IET",
    'version': '1.0',

    'depends': ['base', 'hr', 'account', 'project_time_sheet_total', 'timesheet_accounting'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/views.xml',
        # 'views/res_setting_overtime.xml',
        'views/menus.xml',
    ],
    'installable': True,
    "license": "AGPL-3",
    'application': False,

}
