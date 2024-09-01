# -*- coding: utf-8 -*-
{
    'name': "apte_sales_report",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Tareq Aljezawi | IET",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale'],

    # always loaded
    'data': [
        #'security/security.xml',
        'views/pivot_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',

    ],
}

