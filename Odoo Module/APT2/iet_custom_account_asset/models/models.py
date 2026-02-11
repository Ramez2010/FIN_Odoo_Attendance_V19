# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class iet_custom_account_asset(models.Model):
#     _name = 'iet_custom_account_asset.iet_custom_account_asset'
#     _description = 'iet_custom_account_asset.iet_custom_account_asset'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
