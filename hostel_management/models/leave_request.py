from odoo import models, fields, api


class LeaveRequest(models.Model):
    _name = "leave.request"
    _description = "Leave Request"
    _rec_name = "name_id"

    name_id = fields.Many2one('student', string="Student Name", required=True)
    leave_date = fields.Date(required=True)
    arrival_date = fields.Date(required=True)
    state = fields.Selection([
        ('new','New'),
        ('approved','Approved')
    ], default="new")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, index=True, store=True )
    user_id = fields.Many2one('res.users', string="Related User", default=lambda self: self.env.user, invisible=True)
    duration = fields.Char()

    def approval_button(self):
        self.write({'state': 'approved'})
        student = self.name_id
        room = student.room_id
        if room and room.bed_booked == 1:
            other_leave = self.env['leave.request'].search([
                ('name', '=', student.id),
                ('state', '=', 'approved'),
            ])
            if other_leave:
                cleaning_service = self.env['cleaning.service'].create({
                    'room_id': room.id,
                    'start_time': fields.Datetime.now(),
                    'state': 'new',
                })
                room.state = 'cleaning'





