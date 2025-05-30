from odoo import models, fields, api
from odoo.exceptions import UserError


class StudentReportWizard(models.TransientModel):
    _name = 'student.report.wizard'
    _description = 'Student Report Wizard'

    student_id = fields.Many2one('student', string='Student')
    room_id = fields.Many2one('room.management', string='Room')

    def generate_report(self):
        query = """
                SELECT
                    s.name,
                    s.id AS student_id,
                    r.pending_amount AS pending_amount,
                    r.name AS room_name
                FROM student s
                LEFT JOIN room_management r ON s.room_id = r.id
            """

        if self.student_id and self.room_id:
            query += " WHERE s.id = %s AND r.id = %s"
            self.env.cr.execute(query, (self.student_id.id,self.room_id.id,))
        elif self.student_id:
            query += " WHERE s.id = %s"
            self.env.cr.execute(query, (self.room_id.id,))
        elif self.room_id:
            query += " WHERE r.id = %s"
            self.env.cr.execute(query, (self.room_id.id,))
        else:
            self.env.cr.execute(query)

        result = self.env.cr.dictfetchall()

        for record in result:
            unpaid = self.env['account.move'].search_count([
                ('student_id', '=', record['student_id']),
                ('move_type', '=', 'out_invoice'),
                ('payment_state', '!=', 'paid')
            ])
            record['invoice_status'] = 'Pending' if unpaid else 'Done'
        data = {
            'records': result,
            'report_type': 'student',
            'student_name': self.student_id.name if self.student_id else '',
            'room_name': self.room_id.name if self.room_id else '',
            'report_title': 'Students Report',
            'table_headers': ['SL.No', 'Student', 'Pending Amount', 'Room', 'Invoice Status']
        }
        return self.env.ref('hostel_management.student_report_action').report_action(self, data=data)