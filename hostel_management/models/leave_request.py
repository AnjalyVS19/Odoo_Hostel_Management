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
        self.write({'state': 'approved'})
        student = self.name
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