# -*- coding: utf-8 -*-
{
    'name': "iet_import_product_from_excel",
    'author': "IET",
    'category': 'Uncategorized',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['base', 'report_xlsx', 'stock', 'arabic_product_name', 'product_barcode'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_move_line.xml',
        'wizard/wizard_view.xml',
        'views/server_action.xml',
    ],
    # 'external_dependencies': {
    #     'python': ['pandas', 'openpyxl'],
    # },
    'installable': True,
    'application': False,
}
