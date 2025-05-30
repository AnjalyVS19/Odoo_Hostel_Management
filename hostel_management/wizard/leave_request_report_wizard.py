from odoo import fields, models


class LeaveRequestReportWizard(models.TransientModel):
    _name = 'leave.request.report.wizard'
    _description = 'Filter for Leave Request Report'

    student_id = fields.Many2one('student', string="Student")
    room_id = fields.Many2one('room.management', string="Room")
    leave_date = fields.Date(string="Start Date")
    arrival_date = fields.Date(string="Arrival Date")
    duration = fields.Char()
    report_type = fields.Char()

    def action_print_report(self):
        query = """
           SELECT
                s.name, s.id as student_id, r.name AS room_name,
                l.leave_date, l.arrival_date, (l.arrival_date - l.leave_date) AS duration
            FROM student s
            LEFT JOIN room_management r ON s.room_id = r.id
            LEFT JOIN leave_request l ON l.name_id = s.id  
        """
        
        if self.student_id and self.room_id:
            query += " WHERE s.id = %s AND r.id = %s"
            self.env.cr.execute(query, (self.student_id.id, self.room_id.id,))

        elif self.student_id and self.leave_date:
            query += " WHERE s.id = %s AND leave_date >= %s"
            self.env.cr.execute(query, (self.student_id.id, self.leave_date,))

        elif self.student_id and self.arrival_date:
            query += " WHERE s.id = %s AND l.arrival_date <= %s"
            self.env.cr.execute(query, (self.student_id.id, self.arrival_date,))


        elif self.room_id and self.leave_date:
            query += " WHERE r.id = %s AND l.leave_date >= %s"
            self.env.cr.execute(query, (self.room_id.id, self.leave_date,))

        elif self.room_id and self.arrival_date:
            query += " WHERE r.id = %s AND l.arrival_date <= %s"
            self.env.cr.execute(query, (self.room_id.id, self.arrival_date,))


        elif self.leave_date and self.arrival_date:
            query += " WHERE l.leave_date >= %s AND l.arrival_date <= %s"
            self.env.cr.execute(query, (self.leave_date, self.arrival_date,))

        elif self.student_id:
            query += " WHERE s.id = %s"
            self.env.cr.execute(query, (self.student_id.id,))

        elif self.room_id:
            query += " WHERE r.id = %s"
            self.env.cr.execute(query, (self.room_id.id,))
        
        elif self.leave_date:
            query += " WHERE l.leave_date >= %s"
            self.env.cr.execute(query, (self.leave_date,))
        
        elif self.arrival_date:
            query += " WHERE l.arrival_date <= %s"
            self.env.cr.execute(query, (self.arrival_date,))

        result = self.env.cr.dictfetchall()
        
        data = {
            'records': result,
            'report_type': 'leave',
            'student_name': self.student_id.name if self.student_id else '',
            'room_name': self.room_id.name if self.room_id else '',
            'report_title': 'Students Leave Request Report',
            'table_headers': ['SL.No', 'Student', 'Room', 'Start Date', 'Arrival Date', 'Duration']
        }
        
        return self.env.ref('hostel_management.leave_report_action').report_action(self, data=data)
        
