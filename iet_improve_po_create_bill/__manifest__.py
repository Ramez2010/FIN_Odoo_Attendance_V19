# -*- coding: utf-8 -*-
{
    'name': "Improve PO, SO and Stock",
    'author': "IET / Noura",
    'category': 'Uncategorized',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['base', 'purchase', 'sale', 'project', 'stock', 'sale_project','account'],
    'data': [
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'views/project.xml',
        'views/picking_return.xml',
    ],
    "assets": {
        "web.assets_backend": [
            "iet_improve_po_create_bill/static/src/js/product_label.js",
        ],
    },
    'installable': True,
    'application': False,
}
