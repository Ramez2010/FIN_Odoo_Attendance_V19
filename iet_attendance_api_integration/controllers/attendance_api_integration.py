# -*- coding: utf-8 -*-

from odoo import fields, http
from odoo.exceptions import AccessError
from odoo.http import request
import json
import logging
import functools
logger = logging.getLogger(__name__)

from odoo.exceptions import AccessDenied

def check_attendance_login_user(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        args_data = request.httprequest.data.decode()
        if not args_data:
            return request.make_json_response({
                "Missing Error": "Data Is Missing"
            }, status=400)
        data = json.loads(args_data)
        if not data.get("token"):
            return request.make_json_response({
                "Missing Error": "Token Is Missing"
            }, status=400)
        token = data.get("login")
        try:
            current_user_id = request.env["res.users"].sudo().search([("user_access_token", "=", token)], limit=1)
            if current_user_id:
                if current_user_id.user_access_token_expiry_date and (
                        fields.datetime.now() > current_user_id.user_access_token_expiry_date):
                    return request.make_json_response({
                        "Error": "Token Expired, Please Check The New Token."
                    }, status=400)
            if not current_user_id:
                return request.make_json_response({
                    "Error": "Incorrect Token, try again."
                }, status=400)
            request.params['login_success'] = True
        except AccessError as ae:
            return request.make_json_response({
                "Access Error": f"Error: {ae.name}"
            }, status=400)
        except AccessDenied as ad:
            return request.make_json_response({
                "Access Denied": "invalid Token"
            }, status=400)
        except Exception as e:
            logger.error("Not Valid {}".format((e)))
            return request.make_json_response({
                "Not Valid {}".format((e)): "invalid_data"
            }, status=400)
        return func(self, *args, **kwargs)
    return wrapper


class AttendanceApiController(http.Controller):

    @check_attendance_login_user
    @http.route('/api/attendance/analytic_accounts', methods=["GET"], type='http', auth="none", csrf=False)
    def get_analytic_accounts(self):
        args = request.httprequest.data.decode()
        data = json.loads(args)
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
                    "name": analytic_account.name,
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


