# -*- coding: utf-8 -*-
{
    'name': "iet_sale_order_custom",
    'author': "IET",
    'version': '1.0',
    'depends': ['base', 'sale', 'project', 'hr', 'custom_analytic_account'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_order_view.xml',
        'views/project_view.xml',
    ],
    'license': 'LGPL-3',
}
