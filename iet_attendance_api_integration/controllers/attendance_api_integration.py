# -*- coding: utf-8 -*-

from odoo import fields, http
from odoo.exceptions import AccessError
from odoo.http import request
import json
import logging
import functools
logger = logging.getLogger(__name__)

from odoo.exceptions import AccessDenied
from odoo.addons.iet_api_access_token.controllers.main import authorization



class AttendanceApiController(http.Controller):

    @authorization
    @http.route('/api/attendance/analytic_accounts', methods=["GET"], type='http', auth="none", csrf=False)
    def get_analytic_accounts(self):
        args = request.httprequest.data.decode()
        data = request.params
        domain = []
        analytic_accounts_data = []
        if data.get("company_id"):
            data_company_id = int(data.get("company_id"))
        else:
            data_company_id = 0
        if data_company_id > 0:
            domain.append(("company_id", "=", data_company_id))
        analytic_account_ids = request.env["account.analytic.account"].sudo().search(domain)
        if analytic_account_ids:
            for analytic_account in analytic_account_ids:
                analytic_accounts_data.append({
                    "name": f"[{analytic_account.code}] {analytic_account.name}",
                    "combined_name": f"[{analytic_account.code}] {analytic_account.name}",
                    "id": analytic_account.id,
                    "code": analytic_account.code,
                    "credit": analytic_account.credit,
                    "debit": analytic_account.debit,
                    "balance": analytic_account.balance,
                })
        if analytic_accounts_data:
            return request.make_json_response({
                "message": "Analytic Accounts Loaded Successfully",
                "result": analytic_accounts_data
            }, status=200)
        else:
            return request.make_json_response({
                "Error": f"NO Analytic Accounts Founded"
            }, status=400)
