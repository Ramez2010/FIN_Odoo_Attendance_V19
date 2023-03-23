from odoo import  fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'
    # translate account name
    name = fields.Char(translate=True)

    