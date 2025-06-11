from odoo import models, fields

class StudentReportWizard(models.TransientModel):
    _name = 'student.report.wizard'
    _description = 'Student Report Wizard'

    student_ids = fields.Many2many('student', string='Student')
    room_ids = fields.Many2many('room.management', string='Room')

    def generate_report(self):
        query = """
                SELECT
                    s.name,
                    s.id AS student_ids,
                    r.pending_amount AS pending_amount,
                    r.name AS room_name
                FROM student s
                INNER JOIN room_management r ON s.room_id = r.id
            """

        if self.student_ids and self.room_ids:
            query += " WHERE s.id IN %s AND r.id IN %s"
            self.env.cr.execute(query, (tuple(self.student_ids.ids), tuple(self.room_ids.ids)))
        elif self.student_ids:
            query += " WHERE s.id IN %s"
            self.env.cr.execute(query, (tuple(self.student_ids.ids),))
        elif self.room_ids:
            query += " WHERE r.id IN %s"
            self.env.cr.execute(query, (tuple(self.room_ids.ids),))
        else:
            self.env.cr.execute(query)

        result = self.env.cr.dictfetchall()
        unique_rooms = list(set([rec['room_name'] for rec in result if rec['room_name']]))
        room_name = unique_rooms[0] if len(unique_rooms) == 1 else ''

        for record in result:
            unpaid = self.env['account.move'].search_count([
                ('student_id', '=', record['student_ids']),
                ('move_type', '=', 'out_invoice'),
                ('payment_state', '!=', 'paid')
            ])
            record['invoice_status'] = 'Pending' if unpaid else 'Done'

        data = {
            'records': result,
            'report_type': 'student',
            'student_name': self.student_ids[0].name if len(self.student_ids) == 1 else '',
            'room_name': room_name,
            'report_title': 'Students Report',
            'hide_student_col': len(self.student_ids) == 1,
            'hide_room_col': len(unique_rooms) == 1,
        }
        return self.env.ref('hostel_management.student_report_action').report_action(self, data=data)

    def action_download_xlsx(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/student_report/xlsx?wizard_id=%d' % self.id,
            'target': 'self',
        }
