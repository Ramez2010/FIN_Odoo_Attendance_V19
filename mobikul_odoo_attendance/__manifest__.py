
# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Attendance App for ODOO (Android and IOS)",
  "summary"              :  """Track (checkin or checkout) employee attendence through native mobile(phone)application ( Android and IOS ).""",
  "category"             :  "Human Resources/Attendances",
  "version"              :  "1.0.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/odoo-attendance-mobile-app.html",
  "description"          :  """
                              This module aims to manage employee's attendances with a native mobile application ( Android & IOS ).
                              =====================================================================================================
                              Keeps account of the attendances of the employees on the basis of the
                              actions(Check in/Check out) performed by them.
                              Mobikul Attendence
                              Odoo Attendence
                              Attendance
                              Attndence
                              Mobikul odoo attendance
                              Mobikul odoo attendence
                              Attendence App, Attendnance App""",
  "live_test_url"        :  "https://demo.webkul.com/mobikulAttendance",
  "depends"              :  ['sh_hr_attendance_geolocation', 'hr_attendance'],
  "data"                 :  [
                              'security/mobikul_attendance_security.xml',
                              'security/ir.model.access.csv',
                              'views/res_config_inherit.xml',
                              'views/mobile_attendance_view.xml',
                              'views/attendanceView.xml',
                              'views/fcmView.xml',
                              'views/extraAddedFeature.xml',
                              'views/menus.xml',
                              'data/defaultdata.xml',
                              'data/attendanceSequnce.xml'

                            ],
  "demo"                 :  [],
  "css"                  :  [],
  "js"                   :  [],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  199.0,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
  "external_dependencies": {"python" : ["jwt"]},
}
