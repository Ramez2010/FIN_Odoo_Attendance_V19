# -*- coding: utf-8 -*-
# from odoo import http


# class IetCustomStock(http.Controller):
#     @http.route('/iet_custom_stock/iet_custom_stock', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/iet_custom_stock/iet_custom_stock/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('iet_custom_stock.listing', {
#             'root': '/iet_custom_stock/iet_custom_stock',
#             'objects': http.request.env['iet_custom_stock.iet_custom_stock'].search([]),
#         })

#     @http.route('/iet_custom_stock/iet_custom_stock/objects/<model("iet_custom_stock.iet_custom_stock"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('iet_custom_stock.object', {
#             'object': obj
#         })
