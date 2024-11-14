# -*- coding: utf-8 -*-

import logging
import werkzeug
import json
from jwt.exceptions import DecodeError
from ast import literal_eval
from functools import wraps
from base64 import b64decode
from odoo import http, _,fields,tools
from odoo.fields import Datetime, Date, Selection
from odoo.addons.iet_api_access_token.tools.jwt_token import jwt_encode, jwt_decode
from odoo.http import request
from odoo.exceptions import UserError
from odoo.tools import format_datetime
import logging
import functools
logger = logging.getLogger(__name__)
from odoo.exceptions import AccessError, AccessDenied


_logger = logging.getLogger(__name__)


def get_jwt_token(secret, *args, algorithm = "HS256", **kwargs):
    payload = {
      "partner_id": args[0],
      "user_id": args[1]
    }
    token = jwt_encode(payload, secret, algorithm)
    return token


def authorization(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        """
        Authorize user through the provided jwt token
        """
        response = {'success': False, 'responseCode': 400, 'message': _('Unknown Error !!!')}
        user = False
        # secret = self.secret_key
        secret = "dummySecretKey"
        # token = self._mAuth
        token = request.httprequest.headers.get('Authorization')
        if not token:
            return request.make_json_response({
                "Error": "Token Is Missing"
            }, status=400)
        if token:
            token = token.split(" ")[1]
        try:
            payload = jwt_decode(token, secret, 'HS256')
            USER = request.env['res.users'].sudo()
            if payload:
                user = USER.browse(payload['user_id'])
                if user:
                    response['success'] = True
                    response['responseCode'] = 200
                    response['user'] = user
                    response['message'] = _('Authorized successfully!!!')
        except DecodeError as de:
            _logger.info("this is issue %r", de)
            response['message'] = _('Invalid token')
            response['details'] = _("%s".format(de.args[0]))
            return request.make_json_response(response, status=400)
        return func(self, *args, **kwargs)
    return wrapper


class ApiLoginAccessTokenController(http.Controller):

    @http.route('/api/auth/login', methods=["GET"], type='http', auth="none", csrf=False)
    def authenticate_and_generate_token(self):
        """
        Authenticate user through the login header provided in the header
        """
        response = {'success': False, 'responseCode': 400, 'message': _('Unknown Error !!!')}
        data = request.params
        if not data:
            return request.make_json_response({
                "Missing Error": "Login And Password Are Missing"
            }, status=400)
        if not data.get("login"):
            return request.make_json_response({
                "Missing Error": "Login Is Missing"
            }, status=400)
        if not data.get("password"):
            return request.make_json_response({
                "Missing Error": "Password Is Missing"
            }, status=400)
        login = data.get("login")
        password = data.get("password")
        try:
            current_user_id = request.env["res.users"].sudo().search([("login", "=", login)], limit=1)
            if current_user_id:
                assert password
                request.env.cr.execute(
                    f"SELECT COALESCE(password, '') FROM res_users WHERE id={current_user_id.id}"
                )
                [hashed] = request.env.cr.fetchone()
                ctx = current_user_id._crypt_context()
                pw = ctx.hash(password)
                valid, replacement = current_user_id._crypt_context() \
                    .verify_and_update(password, hashed)
                if not valid:
                    return request.make_json_response({
                        "Error": "Incorrect Password, try again or click on Forgot Password to reset your password."
                    }, status=400)
                request.params['login_success'] = True
                response['success'] = True
                response['responseCode'] = 200
                response['user'] = current_user_id
                response['message'] = 'Success'
                response['authorizeToken'] = get_jwt_token("dummySecretKey", current_user_id.partner_id.id, current_user_id.id)
                return request.make_json_response(response, status=200)
        except AccessError as ae:
            response["message"] = f"{ae}"
            return request.make_json_response(response, status=400)
        except AccessDenied as ad:
            response["message"] = "Access Denied, login or password is not correct"
            response["error_message"] = f"{ad}"
            return request.make_json_response(response, status=400)
        except Exception as e:
            response["message"] = f"{e}"
            logger.error("Not Valid {}".format((e)))
            return request.make_json_response(response, status=400)