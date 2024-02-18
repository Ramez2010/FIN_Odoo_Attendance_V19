# -*- coding: utf-8 -*-

from odoo import models, fields, api
import string


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    arabic_name = fields.Char()

    @api.onchange('arabic_name', 'name')
    def arabic_name_lang(self):
        for rec in self:
            if rec.arabic_name:
                lang = {
                    'ء': 'c', 'ا': 'A', 'إ': 'A',
                    'أ': 'A', 'آ': 'A', 'ب': 'b',
                    'ة': 'o', 'ت': 't', 'ث': 'v',
                    'ج': 'j', 'ح': 'H', 'خ': 'x',
                    'د': 'd', 'ذ': 'V', 'ر': 'r',
                    'ز': 'z', 'س': 's', 'ش': 'E',
                    'ص': 'S', 'ض': 'D', 'ط': 'T',
                    'ظ': 'Z', 'ع': 'C', 'غ': 'g',
                    'ف': 'f', 'ق': 'q', 'ك': 'k',
                    'ل': 'l', 'م': 'm', 'ن': 'n',
                    'ه': 'h', 'ؤ': 'c', 'و': 'w',
                    'ى': 'y', 'ئ': 'c', 'ي': 'y',
                    ' ': ' ', '.': '.', ',': ',', '-': '-', '_': '_', '|': '|', '/': '/',
                }
                ar = list(lang.keys()) + list(string.digits)
                # if any(x not in ar for x in rec.arabic_name):
                #     rec.arabic_name = False
                #     return {'warning': {
                #         'title': "Note:",
                #         'message': "Arabic name must be arabic",
                #     }}
            if rec.name:
                en = list(string.ascii_letters) + list(string.digits)
                # if any(x not in en for x in rec.name):
                #     rec.name = False
                #     return {'warning': {
                #         'title': "Note:",
                #         'message': "Name must be English",
                #     }}


class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    arabic_name = fields.Char(related="product_tmpl_id.arabic_name")

    @api.onchange('arabic_name', 'name')
    def arabic_name_lang(self):
        for rec in self:
            if rec.arabic_name:
                lang = {
                    'ء': 'c', 'ا': 'A', 'إ': 'A',
                    'أ': 'A', 'آ': 'A', 'ب': 'b',
                    'ة': 'o', 'ت': 't', 'ث': 'v',
                    'ج': 'j', 'ح': 'H', 'خ': 'x',
                    'د': 'd', 'ذ': 'V', 'ر': 'r',
                    'ز': 'z', 'س': 's', 'ش': 'E',
                    'ص': 'S', 'ض': 'D', 'ط': 'T',
                    'ظ': 'Z', 'ع': 'C', 'غ': 'g',
                    'ف': 'f', 'ق': 'q', 'ك': 'k',
                    'ل': 'l', 'م': 'm', 'ن': 'n',
                    'ه': 'h', 'ؤ': 'c', 'و': 'w',
                    'ى': 'y', 'ئ': 'c', 'ي': 'y',
                    ' ': ' ', '.': '.', ',': ',', '-': '-', '_': '_', '|': '|', '/': '/',
                }
                ar = list(lang.keys()) + list(string.digits)
                if any(x not in ar for x in rec.arabic_name):
                    rec.arabic_name = False
                    return {'warning': {
                        'title': "Note:",
                        'message': "Arabic name must be arabic",
                    }}
            if rec.name:
                en = list(string.ascii_letters) + list(string.digits)
                if any(x not in en for x in rec.name):
                    rec.name = False
                    return {'warning': {
                        'title': "Note:",
                        'message': "Name must be English",
                    }}


class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    arabic_name = fields.Char(related="product_id.arabic_name")


# class PurchaseRequestLineInherit(models.Model):
#     _inherit = 'purchase.request.line'
#
#     arabic_name = fields.Char(related="product_id.arabic_name")
#

# class MaterialRequestLineInherit(models.Model):
#     _inherit = 'material.request.line'
#
#     arabic_name = fields.Char(related="product_id.arabic_name")
