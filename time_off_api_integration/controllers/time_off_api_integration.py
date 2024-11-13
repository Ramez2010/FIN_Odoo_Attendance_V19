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
from odoo.addons.iet_api_access_token.tools.jwt_token import jwt_encode, jwt_decode
import base64


class TimeOffApiController(http.Controller):


    @authorization
    @http.route('/api/time_off/type', methods=["GET"], type='http', auth="none", csrf=False)
    def get_time_off_type(self):
        data = []
        holiday_status_ids = request.env["hr.leave.type"].sudo().search([])
        if holiday_status_ids:
            for holiday in holiday_status_ids:
                data.append({
                    "name": holiday.name,
                    "id": holiday.id,
                    "requires_allocation": holiday.requires_allocation,
                    "allocation_validation_type": holiday.allocation_validation_type,
                    "request_unit": holiday.request_unit,
                })
        if data:
            return request.make_json_response({
                "message": "Time Off Types Loaded Successfully",
                "result": data
            }, status=200)
        else:
            return request.make_json_response({
                "Error": f"No Time Off Types Founded"
            }, status=400)

    @authorization
    @http.route('/api/time_off/public_holidays', methods=["GET"], type='http', auth="none", csrf=False)
    def get_public_holidays(self):
        args = request.httprequest.data.decode()
        data = request.params
        domain = []
        public_holiday_data = []
        if data.get("month"):
            data_month = int(data.get("month"))
            data_year = int(data.get("year"))
            if not data_year:
                return request.make_json_response({
                    "Missing Error": "Year Is Missing"
                }, status=400)
        else:
            data_month = 0
        if data.get("company_id"):
            data_company_id = int(data.get("company_id"))
        else:
            data_company_id = 0
        if data_company_id > 0:
            domain.append(("company_id", "=", data_company_id))
        public_holiday_ids = request.env["resource.calendar.leaves"].sudo().search(domain)
        if public_holiday_ids:
            if data_month > 0:
                public_holiday_ids = public_holiday_ids.filtered(lambda p: p.date_from.date().month == data_month and
                                                                           p.date_from.date().year == data_year)
            for public_holiday in public_holiday_ids:
                public_holiday_data.append({
                    "name": public_holiday.name,
                    "id": public_holiday.id,
                    "date_from": public_holiday.date_from,
                    "date_to": public_holiday.date_to,
                    "working_hours": public_holiday.calendar_id.name,
                    "work_entry_type": public_holiday.work_entry_type_id.name,
                })
        if public_holiday_data:
            return request.make_json_response({
                "message": "Public Holidays Loaded Successfully",
                "result": public_holiday_data
            }, status=200)
        else:
            return request.make_json_response({
                "Error": f"NO Public Holidays Founded"
            }, status=400)

    @authorization
    @http.route('/api/employees', methods=["GET"], type='http', auth="none", csrf=False)
    def get_all_employees(self):
        data = request.params
        domain = []
        employees_data = []
        if data.get("company_id"):
            data_company_id = int(data.get("company_id"))
        else:
            data_company_id = 0
        if data_company_id > 0:
            domain.append(("company_id", "=", data_company_id))
        employee_ids = request.env["hr.employee"].sudo().search(domain)
        if employee_ids:
            for employee in employee_ids:
                employees_data.append({
                    "name": employee.name,
                    "id": employee.id,
                    "company_name": employee.company_id.name,
                    "company_id": employee.company_id.id,
                })
        if employees_data:
            return request.make_json_response({
                "message": "Employees Loaded Successfully",
                "result": employees_data
            }, status=200)
        else:
            return request.make_json_response({
                "Error": f"NO Employees Founded"
            }, status=400)

    @authorization
    @http.route('/api/time_off/create', methods=["POST"], type='http', auth="none", csrf=False)
    def time_off_create(self):
        args = request.httprequest.data.decode()
        if not args:
            return request.make_json_response({
                "Missing Error": "Data Is Missing"
            }, status=400)
        data = json.loads(args)
        if not data.get("employee_id"):
            return request.make_json_response({
                "Missing Error": "employee_id Is Missing"
            }, status=400)
        if not data.get("time_off_type_id"):
            return request.make_json_response({
                "Missing Error": "time_off_type_id Is Missing"
            }, status=400)
        if not data.get("date_from"):
            return request.make_json_response({
                "Missing Error": "date_from Is Missing"
            }, status=400)
        if not data.get("date_to"):
            return request.make_json_response({
                "Missing Error": "date_to Is Missing"
            }, status=400)
        employee_id = int(data.get("employee_id"))
        holiday_status_id = int(data.get("time_off_type_id"))
        date_from = fields.Date.from_string(data.get("date_from"))
        date_to = fields.Date.from_string(data.get("date_to"))
        try:
            employee = request.env["hr.employee"].sudo().browse(employee_id)
            holiday_status = request.env["hr.leave.type"].sudo().browse(holiday_status_id)
            if data.get("description"):
                name = data.get("description")
            else:
                name = f"{employee.name} {holiday_status.name} Time Off"
            holiday_id = request.env["hr.leave"].sudo().create({
                "name": name,
                "holiday_type": "employee",
                "employee_id": employee_id,
                "holiday_status_id": holiday_status_id,
                "request_date_from": date_from,
                "request_date_to": date_to,
                "notes": data.get("notes") if data.get("notes") else False
            })
            if holiday_id:
                # Create Attachments And Add Them To Leave Request
                attachment_ids = []
                attachment_list = request.httprequest.files.getlist('attachment_ids')
                if attachment_list:
                    for att in attachment_list:
                        attachments = {
                            'res_name': att.filename,
                            'res_model': 'hr.leave.request',
                            'res_id': holiday_id.sudo().id,
                            'datas': base64.encodebytes(att.read()),
                            'type': 'binary',
                            'name': att.filename,
                        }
                        attachment_obj = http.request.env['ir.attachment']
                        att_record = attachment_obj.sudo().create(attachments)
                        attachment_ids.append(att_record.id)
                if attachment_ids:
                    holiday_id.sudo().update({'attachment_ids': [(6, 0, attachment_ids)]})
                return request.make_json_response({
                    "message": "Time Off Created Successfully",
                    "result": {
                        "name": holiday_id.name,
                        "id": holiday_id.id,
                        "employee": holiday_id.employee_id.name,
                        "employee_id": holiday_id.employee_id.id,
                        "time_off_type": holiday_id.holiday_status_id.name,
                        "time_off_type_id": holiday_id.holiday_status_id.id,
                        "date_from": holiday_id.request_date_from,
                        "date_to": holiday_id.request_date_to,
                        "duration": holiday_id.number_of_days,
                        "state": holiday_id.state,
                        "notes": holiday_id.notes,
                    }
                }, status=201)
            else:
                return request.make_json_response({
                    "Error": "Invalid Data"
                }, status=400)
        except Exception as error:
            logger.error(error)
            return request.make_json_response({
                "Error": "Invalid Data"
            }, status=400)

    @authorization
    @http.route('/api/time_off/update/<int:time_off_id>', methods=["PATCH"], type='http', auth="none", csrf=False)
    def time_off_update(self, time_off_id):
        args = request.httprequest.data.decode()
        if not args:
            return request.make_json_response({
                "Missing Error": "Data Is Missing"
            }, status=400)
        data = json.loads(args)
        updated_data = {"is_updated": True}
        if not time_off_id:
            return request.make_json_response({
                "Missing Error": "time_off_id Is Missing"
            }, status=400)
        if data.get("time_off_type_id"):
            updated_data.update({"holiday_status_id": int(data.get("time_off_type_id"))})
        if data.get("date_from"):
            updated_data.update({"request_date_from": fields.Date.from_string(data.get("date_from"))})
        if data.get("date_to"):
            updated_data.update({"request_date_to": fields.Date.from_string(data.get("date_to"))})
        if data.get("description"):
            updated_data.update({"name": data.get("description")})
        if data.get("notes"):
            updated_data.update({"notes": data.get("notes")})
        holiday_id = int(time_off_id)
        try:
            holiday = request.env["hr.leave"].sudo().browse(holiday_id)
            if holiday.state != 'validate':
                holiday.sudo().write(updated_data)
                # Create Attachments And Add Them To Leave Request
                attachment_ids = []
                attachment_list = request.httprequest.files.getlist('attachment_ids')
                if attachment_list:
                    for att in attachment_list:
                        attachments = {
                            'res_name': att.filename,
                            'res_model': 'hr.leave.request',
                            'res_id': holiday.sudo().id,
                            'datas': base64.encodebytes(att.read()),
                            'type': 'binary',
                            'name': att.filename,
                        }
                        attachment_obj = http.request.env['ir.attachment']
                        att_record = attachment_obj.sudo().create(attachments)
                        attachment_ids.append(att_record.id)
                if attachment_ids:
                    holiday.sudo().update({'attachment_ids': [(6, 0, attachment_ids)]})
                return request.make_json_response({
                    "message": "Time Off Updated Successfully",
                    "result": {
                        "name": holiday.name,
                        "id": holiday.id,
                        "employee": holiday.employee_id.name,
                        "employee_id": holiday.employee_id.id,
                        "time_off_type": holiday.holiday_status_id.name,
                        "time_off_type_id": holiday.holiday_status_id.id,
                        "date_from": holiday.request_date_from,
                        "date_to": holiday.request_date_to,
                        "duration": holiday.number_of_days,
                        "state": holiday.state,
                        "notes": holiday.number_of_days,
                        "is_updated": holiday.is_updated,
                    }
                }, status=200)
            else:
                return request.make_json_response({
                    "Error": "We Can Not Approve This Action, Time Off Already Approved"
                }, status=400)
        except Exception as error:
            logger.error(error)
            return request.make_json_response({
                "Error": "Invalid Time Off"
            }, status=400)

    @authorization
    @http.route('/api/time_off/unlink/<int:time_off_id>', methods=["DELETE"], type='http', auth="none", csrf=False)
    def time_off_unlink(self, time_off_id):
        if not time_off_id:
            return request.make_json_response({
                "Missing Error": "time_off_id Is Missing"
            }, status=400)
        try:
            holiday_id = int(time_off_id)
            holiday = request.env["hr.leave"].sudo().browse(holiday_id)
            secret = "dummySecretKey"
            token = request.httprequest.headers.get('Authorization')
            if token:
                token = token.split(" ")[1]
                payload = jwt_decode(token, secret, 'HS256')
                USER = request.env['res.users'].sudo()
                if payload:
                    current_user_id = USER.browse(payload['user_id'])
                    if current_user_id:
                        if holiday.state != 'validate':
                            # holiday.sudo().action_draft()
                            holiday.with_user(current_user_id.id).unlink()
                            return request.make_json_response({
                                "message": "Time Off Deleted Successfully",
                            }, status=202)
                        else:
                            return request.make_json_response({
                                "Error": "Invalid time_off_id"
                            }, status=400)
        except Exception as error:
            logger.error(error)
            return request.make_json_response({
                "Error": f"{error}"
            }, status=400)

    @authorization
    @http.route('/api/time_off/employee/<int:employee_id>', methods=["GET"], type='http', auth="none", csrf=False)
    def get_employee_time_off(self, employee_id):
        data = request.params
        if not employee_id:
            return request.make_json_response({
                "Missing Error": "employee_id Is Missing"
            }, status=400)
        leave_data = []
        employee_id = int(employee_id)
        domain = [("employee_id", "=", employee_id)]
        if data.get("state"):
            domain.append(("state", "=", data.get("state")))
        if data.get("month"):
            data_month = int(data.get("month"))
            data_year = int(data.get("year"))
            if not data_year:
                return request.make_json_response({
                    "Missing Error": "Year Is Missing"
                }, status=400)
        else:
            data_month = 0
        try:
            leave_ids = request.env["hr.leave"].sudo().search(domain)
            if leave_ids:
                if data_month > 0:
                    leave_ids = leave_ids.filtered(
                        lambda l: l.request_date_from.month == data_month and
                                  l.request_date_from.year == data_year)
                for leave in leave_ids:
                    leave_data.append({
                        "name": leave.name,
                        "id": leave.id,
                        "employee": leave.employee_id.name,
                        "employee_id": leave.employee_id.id,
                        "time_off_type": leave.holiday_status_id.name,
                        "time_off_type_id": leave.holiday_status_id.id,
                        "date_from": leave.request_date_from,
                        "date_to": leave.request_date_to,
                        "duration": leave.number_of_days,
                        "state": leave.state,
                    })
            if leave_data:
                return request.make_json_response({
                    "message": "Employee Time Off Loaded Successfully",
                    "result": data
                }, status=200)
            else:
                return request.make_json_response({
                    "Missing Error": "No Time Off For This Employee"
                }, status=400)
        except Exception as error:
            logger.error(error)
            return request.make_json_response({
                "Error": f"{error}"
            }, status=400)

    @authorization
    @http.route('/api/time_off/<int:time_off_id>', methods=["GET"], type='http', auth="none", csrf=False)
    def get_single_time_off(self, time_off_id):
        if not time_off_id:
            return request.make_json_response({
                "Error": "Invalid time_off_id"
            }, status=400)
        try:
            holiday_id = request.env["hr.leave"].sudo().browse(time_off_id)
            if holiday_id:
                return request.make_json_response({
                    "message": "Time Off Loaded Successfully",
                    "result": {
                        "name": holiday_id.name,
                        "id": holiday_id.id,
                        "employee": holiday_id.employee_id.name,
                        "employee_id": holiday_id.employee_id.id,
                        "time_off_type": holiday_id.holiday_status_id.name,
                        "time_off_type_id": holiday_id.holiday_status_id.id,
                        "date_from": holiday_id.request_date_from,
                        "date_to": holiday_id.request_date_to,
                        "duration": holiday_id.number_of_days,
                        "state": holiday_id.state,
                        "notes": holiday_id.notes,
                    }
                }, status=200)
            else:
                return request.make_json_response({
                    "Error": "Invalid time_off_id"
                }, status=400)
        except Exception as error:
            logger.error(error)
            return request.make_json_response({
                "Error": "Invalid time_off_id"
            }, status=400)


