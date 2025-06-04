from odoo import fields, models


class LeaveRequestReportWizard(models.TransientModel):
    _name = 'leave.request.report.wizard'
    _description = 'Filter for Leave Request Report'

    student_ids = fields.Many2many('student', string="Student")
    room_ids = fields.Many2many('room.management', string="Room")
    leave_date = fields.Date(string="Leave Date")
    arrival_date = fields.Date(string="Arrival Date")
    duration = fields.Char()

    def action_print_report(self):
        query = """
            SELECT
                s.name, s.id as student_ids, r.name AS room_name,
                l.leave_date, l.arrival_date, (l.arrival_date - l.leave_date) AS duration
            FROM student s
            LEFT JOIN room_management r ON s.room_id = r.id
            INNER JOIN leave_request l ON l.name_id = s.id
        """

        if self.student_ids and self.room_ids:
            query += " WHERE s.id IN %s AND r.id IN %s"
            self.env.cr.execute(query, (tuple(self.student_ids.ids), tuple(self.room_ids.ids)))

        elif self.student_ids and self.leave_date:
            query += " WHERE s.id IN %s AND l.leave_date = %s"
            self.env.cr.execute(query, (tuple(self.student_ids.ids), self.leave_date))

        elif self.student_ids and self.arrival_date:
            query += " WHERE s.id IN %s AND l.arrival_date = %s"
            self.env.cr.execute(query, (tuple(self.student_ids.ids), self.arrival_date))

        elif self.room_ids and self.leave_date:
            query += " WHERE r.id IN %s AND l.leave_date = %s"
            self.env.cr.execute(query, (tuple(self.room_ids.ids), self.leave_date))

        elif self.room_ids and self.arrival_date:
            query += " WHERE r.id IN %s AND l.arrival_date = %s"
            self.env.cr.execute(query, (tuple(self.room_ids.ids), self.arrival_date))

        elif self.leave_date and self.arrival_date:
            query += " WHERE l.leave_date = %s AND l.arrival_date = %s"
            self.env.cr.execute(query, (self.leave_date, self.arrival_date))

        elif self.student_ids:
            query += " WHERE s.id IN %s"
            self.env.cr.execute(query, (tuple(self.student_ids.ids),))

        elif self.room_ids:
            query += " WHERE r.id IN %s"
            self.env.cr.execute(query, (tuple(self.room_ids.ids),))

        elif self.leave_date:
            query += " WHERE l.leave_date = %s"
            self.env.cr.execute(query, (self.leave_date,))

        elif self.arrival_date:
            query += " WHERE l.arrival_date = %s"
            self.env.cr.execute(query, (self.arrival_date,))

        else:
            self.env.cr.execute(query)

        result = self.env.cr.dictfetchall()
        unique_rooms = list(set([rec['room_name'] for rec in result if rec['room_name']]))
        room_name = unique_rooms[0] if len(unique_rooms) == 1 else ''

        data = {
            'records': result,
            'report_type': 'leave',
            'student_name': self.student_ids[0].name if len(self.student_ids) == 1 else '',
            'room_name': room_name,
            'report_title': 'Students Leave Request Report',
            'hide_student_col': len(self.student_ids) == 1,
            'hide_room_col': len(unique_rooms) == 1,
            'leave_date': self.leave_date,
            'arrival_date': self.arrival_date,
            'table_headers': ['SL.No', 'Student', 'Room', 'Start Date', 'Arrival Date', 'Duration']
        }

        return self.env.ref('hostel_management.leave_report_action').report_action(self, data=data)

    def action_download_xlsx_leave(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/leave_report/xlsx?wizard_id=%d' % self.id,
            'target': 'self',
        }
