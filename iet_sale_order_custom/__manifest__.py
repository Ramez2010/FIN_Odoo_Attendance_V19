# -*- coding: utf-8 -*-
{
    'name': "iet_sale_order_custom",
    'author': "IET",
    'version': '16',
    'depends': ['base', 'sale', 'project', 'hr', 'custom_analytic_account'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_order_view.xml',
        'views/project_view.xml',
    ],
}
