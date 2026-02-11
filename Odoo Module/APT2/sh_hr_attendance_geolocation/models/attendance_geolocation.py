# Part of Softhealer Technologies.

from odoo import models, fields, api
import json


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    def write(self, vals):
        self.env.registry.clear_cache()
        if self.key == 'google_map_api_key' and vals.get('value') != '/':
            geo_id = self.env['attendance.geolocation.child'].sudo().search([
            ], limit=1)
            if geo_id:
                geo_id.write({'name': "https://maps.googleapis.com/maps/api/js?key=" +
                              vals.get('value')+"&callback=initMap&libraries=visualization"})
        return super(IrConfigParameter, self).write(vals)


class GeolocationChild(models.Model):
    _name = "attendance.geolocation.child"
    _description = 'Attendance GEO Child'

    geo_id = fields.Many2one('attendance.geolocation')
    name = fields.Char("Name")


class Geolocation(models.Model):
    _name = "attendance.geolocation"
    _description = 'Attendance GEO'

    name = fields.Char("Name")
    employee_ids = fields.Many2many("hr.employee", string="Employees")
    employee_domain = fields.Char(compute="_compute_employee_domain")
    from_date = fields.Date("From Date", default=fields.Date.today())
    to_date = fields.Date("To Date", default=fields.Date.today())
    department_id = fields.Many2one('hr.department', string="Department")
    job_id = fields.Many2one('hr.job', string="Job Position")
    child_ids = fields.One2many(
        'attendance.geolocation.child', 'geo_id', string="Child Ids")

    def search_result(self):
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def clear_result(self):
        self.write({'employee_ids': [(6, 0, [])],
                    'department_id': False, 'job_id': False})
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.depends('department_id', 'job_id')
    def _compute_employee_domain(self):
        for rec in self:
            dom = []
            partner_list = []
            if rec.department_id:
                dom.append(('department_id', '=', rec.department_id.id))
            if rec.job_id:
                dom.append(('job_id', '=', rec.job_id.id))

            partner_obj = self.env['hr.employee'].search(dom)
            for partner_id in partner_obj:
                partner_list.append(partner_id.id)

            if partner_list:
                rec.employee_domain = json.dumps([('id', 'in', partner_list)])
            else:
                rec.employee_domain = "[]"