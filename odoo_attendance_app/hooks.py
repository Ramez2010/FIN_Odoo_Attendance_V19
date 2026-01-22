# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def _safe_unlink(env, xmlid):
    record = env.ref(xmlid, raise_if_not_found=False)
    if record and record.exists():
        record.unlink()


def post_init_cleanup_transfer_actions(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _safe_unlink(env, 'odoo_attendance_app.action_attendance_timesheet_transfer_wizard')
    _safe_unlink(env, 'odoo_attendance_app.action_attendance_timesheet_transfer_from_list')
    _safe_unlink(env, 'odoo_attendance_app.menu_odoo_attendance_timesheet_transfer')
