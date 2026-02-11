# -*- coding: utf-8 -*-
{
    'name': 'FIN Attendance',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Mobile attendance tracking with GPS, analytics, and time-off management',
    'description': """
FIN Attendance - Mobile Employee Attendance System
========================================================

Features:
---------
* Mobile app authentication with device binding
* GPS-enabled check-in/check-out with reverse geocoding  
* Analytic account selection per attendance
* Optional selfie capture for attendance verification
* Time-off request submission from mobile
* Leave balance tracking
* Bilingual support (English/Arabic)
* REST API for Flutter mobile application

Technical:
----------
* JWT-based authentication
* bcrypt password hashing
* Device binding (one device per employee)
* Extends hr.attendance and account.analytic.account models
* Custom REST API controllers
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'hr_attendance',
        'hr_holidays',
        'analytic',
    ],
    'external_dependencies': {
        'python': ['jwt', 'bcrypt', 'requests'],
    },
    'data': [
        'security/odoo_attendance_security.xml',
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/odoo_attendance_employee_views.xml',
        'views/vehicle_views.xml',
        'views/fleet_trip_views.xml',
        'views/odoo_attendance_session_views.xml',
        'views/hr_attendance_views.xml',
        'views/account_analytic_views.xml',
        'views/app_config_views.xml',
        'views/attachment_views.xml',
        'views/inbox_message_views.xml',
        'views/far_away_result_views.xml',
        'views/live_map_views.xml',
        'views/hr_employee_extension_views.xml',
        'views/employee_task_views.xml',
        'views/menu_items.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_attendance_app/static/src/xml/live_map.xml',
            'odoo_attendance_app/static/src/js/live_map.js',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': [],
    'post_init_hook': 'post_init_cleanup_transfer_actions',
}




