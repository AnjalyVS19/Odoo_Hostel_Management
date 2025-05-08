from odoo import models, fields

class LeaveRequest(models.Model):
    _name = "leave.request"
    _description = "Leave Request"

    name = fields.Many2one('student', string="Student Name", required=True)
    leave_date = fields.Date(required=True)
    arrival_date = fields.Date(required=True)
    state = fields.Selection([
        ('new','New'),
        ('approved','Approved')
    ], default="new")

    def approval_button(self):
        self.write({'state':'approved'})