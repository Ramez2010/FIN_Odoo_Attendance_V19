# -*- coding: utf-8 -*-
{
    'name': "Improve PO, SO and Stock",
    'author': "IET / Noura",
    'category': 'Uncategorized',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['base', 'purchase','sale','project','stock'],
    'data': [
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'views/project.xml',
    ],
    'installable': True,
    'application': False,
}
