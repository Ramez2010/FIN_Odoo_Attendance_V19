# timesheet_accounting/_manifest_.py
{
    'name': 'Timesheet Accounting',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Timesheet accounting and payroll period configuration',
    'author': 'Your Name',
    'depends': ['base', 'account', 'hr_timesheet'],
    'data': [
        'data/cron_job.xml',
        'views/res_setting.xml',
    ],
    'installable': True,
    "license": "AGPL-3",
    'application': False,
}
