from odoo import fields, models, api, _
import uuid
from dateutil.relativedelta import relativedelta


class ResUsers(models.Model):
    _inherit = "res.users"

    user_access_token = fields.Text(string="Access Token", readonly=True)
    user_access_token_expiry_date = fields.Datetime(string="Access Token Expiry Date", readonly=True)

    @api.model
    def _generate_default_access_token(self):
        for rec in self.env["res.users"].sudo().search([("active", "=", True)]):
            rec.user_access_token = str(uuid.uuid4())
            rec.user_access_token_expiry_date = (fields.datetime.now() + relativedelta(months=1))