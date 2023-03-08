{
    'name':
    "Product Moves Report",
    'summary':
    """Product Moves Report        """,
    'description':
    """Product Moves Report """,
    'sequence':
    1,
    'application':
    True,
    'author':
    "Code Flex",
    'website':
    "http://www.yourcompany.com",
    'category':
    'Uncategorized',
    'version':
    '0.1',
    'license':
    'LGPL-3',
    'depends': [
        'base',
        'stock',
        'report_xlsx',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/product_move_report_wizard.xml',
        'wizards/product_move_xlsx_report_wizard.xml',
        'reports/product_move_report.xml',
    ],
    # 'assets': {
    #     'web.report_assets_common': [
    #         "product_movement_report/static/src/css/*",
    #     ],
    #     'web.assets_backend': [
    #         'product_movement_report/static/src/js/action_manager.js',
    #     ],
    # },
    "auto_install":
    True,
}
