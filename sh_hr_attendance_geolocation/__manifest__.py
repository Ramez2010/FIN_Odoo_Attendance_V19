# Part of Softhealer Technologies.

{
    'name': 'Attendance Location Information',
    'version': '16.0.1',
    'category': 'Human Resources',
    "license": "OPL-1",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    'summary': "Attendance Information,Attendance With Map,Check-In Send Message Odoo, Check-Out Send Notes App, Send Login Comments Module, Send Message In Logout, Get Check In Location, Get GeoLocation With Map, Get Check Out Location Odoo",
    'description': """
Do you want to get the location of the user while Check In & Check Out? Do you want to send notes or messages when Check In & Check Out? Attendance location Information is a very unique module which will enhance odoo features with this module you can get Check In & Check Out location of the user with google maps. When User Check In & Check Out in Odoo they can write Message, Comment or any notes""",
    'depends': ['hr', 'barcodes', 'hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/hr_attendance_view.xml',
        'views/attendance_geolocation.xml',
    ],
    'assets': {
        'web.assets_backend': [
            "sh_hr_attendance_geolocation/static/src/xml/attendance.xml",
            'sh_hr_attendance_geolocation/static/src/js/my_attendances.js',
        ],

    },
    'installable': True,
    'auto_install': False,
    "images": ["static/description/background.png", ],
    "live_test_url": "https://youtu.be/uWtmf_nHkdE",
    'application': True,
    "price": 80,
    "currency": "EUR"
}
