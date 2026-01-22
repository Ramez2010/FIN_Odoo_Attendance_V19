# -*- coding: utf-8 -*-
from . import odoo_attendance_employee
from . import odoo_attendance_session
from . import hr_attendance
from . import account_analytic_account
from . import analytic_account_location
from . import app_config
from . import inbox_message
from . import hr_employee_extension
from . import hr_employee_location_latest

# Ensure DB columns exist for lightweight live-location request state.
# This is a guarded, idempotent ALTER TABLE so it is safe to run on startup
# and will avoid RPC errors if the module fields were added but migrations
# have not yet been applied.
try:
    from odoo.tools import config
    from odoo.sql_db import db_connect
    dbname = config.get('db_name') or config.get('db_name', '')
    if dbname:
        with db_connect(dbname).cursor() as cr:
            try:
                cr.execute("ALTER TABLE IF EXISTS public.hr_employee ADD COLUMN IF NOT EXISTS live_location_request_at timestamptz;")
                cr.execute("ALTER TABLE IF EXISTS public.hr_employee ADD COLUMN IF NOT EXISTS live_location_request_state varchar(16) DEFAULT 'none';")
                cr.execute("ALTER TABLE IF EXISTS public.hr_employee ADD COLUMN IF NOT EXISTS live_location_request_attempts integer DEFAULT 0;")
                cr.execute("ALTER TABLE IF EXISTS public.hr_attendance ADD COLUMN IF NOT EXISTS x_timesheet_line_id integer;")
                cr.execute("ALTER TABLE IF EXISTS public.hr_attendance ADD COLUMN IF NOT EXISTS x_timesheet_transferred_at timestamp;")
                cr.commit()
            except Exception:
                # On hosted environments we do not want to fail import if DDL is restricted
                pass
except Exception:
    pass
