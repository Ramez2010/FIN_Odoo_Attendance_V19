# -*- coding: utf-8 -*-
{
    'name': "product_barcode",

    'summary': """
        Adding extra 4 models in configuration products for generating product barcode""",

    'description': """
        Product Barcode Combination
    """,

    'author': "Omar Adel",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'stock', 'account', 'sale'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/main_category.xml',
        'views/vendor_category.xml',
        'views/sub_category.xml',
        'views/serial_category.xml',
        'views/product_template.xml',
        'views/product_product.xml',
        'views/create_receipt.xml',
        'views/account_move.xml',
    ],
}
