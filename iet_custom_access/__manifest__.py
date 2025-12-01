{
    'name': "IET Custom Access",
    'summary': "Restrict Access for Validation, Cancel, and Product Creation",
    'author': "IET",
    'website': "https://www.intelligent-experts.com",
    'category': 'Security',
    'version': '19.0.1.0.0',

    'depends': ['base', 'sale', 'stock', 'product'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}