from odoo import http
from odoo.http import request
import io
import xlsxwriter

class StudentXlsxReportController(http.Controller):

    @http.route(['/student_report/xlsx'], type='http')
    def generate_xlsx_report_student(self, wizard_id=None):
        if not wizard_id:
            return request.not_found()

        wizard = request.env['student.report.wizard'].browse(int(wizard_id))
        if not wizard.exists():
            return request.not_found()

        query = """
            SELECT
                s.name,
                s.id AS student_ids,
                r.pending_amount AS pending_amount,
                r.name AS room_name
            FROM student s
            INNER JOIN room_management r ON s.room_id = r.id
        """

        if wizard.student_ids and wizard.room_ids:
            query += " WHERE s.id IN %s AND r.id IN %s"
            wizard.env.cr.execute(query, (tuple(wizard.student_ids.ids), tuple(wizard.room_ids.ids)))
        elif wizard.student_ids:
            query += " WHERE s.id IN %s"
            wizard.env.cr.execute(query, (tuple(wizard.student_ids.ids),))
        elif wizard.room_ids:
            query += " WHERE r.id IN %s"
            wizard.env.cr.execute(query, (tuple(wizard.room_ids.ids),))
        else:
            wizard.env.cr.execute(query)
        result = wizard.env.cr.dictfetchall()

        students = list(set([rec['name'] for rec in result if rec['name']]))
        rooms = list(set([rec['room_name'] for rec in result if rec['room_name']]))

        unique_student = students[0] if len(students) == 1 else None
        unique_room = rooms[0] if len(rooms) == 1 else None

        for record in result:
            unpaid = wizard.env['account.move'].search_count([
                ('student_id', '=', record['student_ids']),
                ('move_type', '=', 'out_invoice'),
                ('payment_state', '!=', 'paid')
            ])
            record['invoice_status'] = 'Pending' if unpaid else 'Done'

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Student Report')

        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'black',
            'bg_color': '#E0E0E0',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
        })
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'left',
            'valign': 'vcenter'
        })

        main_title = "Student Report"
        worksheet.merge_range(0, 0, 1, 4, main_title, workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#B7DEE8',
            'border': 1
        }))
        row = 3
        max_col = 3

        if len(result) == 1:
            headers = ['SL No', 'Student', 'Room', 'Pending Amount', ' Invoice Status']
            for col, header in enumerate(headers):
                worksheet.write(row, col, header, header_format)
            row += 1

            for i, rec in enumerate(result, start=1):
                col = 0
                worksheet.write(row, col, i, cell_format)
                col += 1
                worksheet.write(row, col, rec['name'], cell_format)
                col += 1
                worksheet.write(row, col, rec['room_name'], cell_format)
                col += 1
                worksheet.write(row, col, rec['pending_amount'], cell_format)
                col += 1
                worksheet.write(row, col, rec['invoice_status'], cell_format)

                row += 1
        else:
            if unique_room:
                worksheet.merge_range(row, 0, row, max_col, f"Room: {unique_room}", title_format)
                row += 1
            if unique_student:
                worksheet.merge_range(row, 0, row, max_col, f"Student: {unique_student}", title_format)
                row += 1

            headers = ['SL No']
            if not unique_student:
                headers.append('Student')
            if not unique_room:
                headers.append('Room')
            headers += ['Pending Amount', ' Invoice Status']

            for col, header in enumerate(headers):
                worksheet.write(row, col, header, header_format)
            row += 1

            for i, rec in enumerate(result, start=1):
                col = 0
                worksheet.write(row, col, i, cell_format)
                col += 1

                if not unique_student:
                    worksheet.write(row, col, rec['name'], cell_format)
                    col+=1
                if not unique_room:
                    worksheet.write(row, col, rec['room_name'], cell_format)
                    col+=1
                worksheet.write(row, col, rec['pending_amount'], cell_format)
                col+=1
                worksheet.write(row, col, rec['invoice_status'], cell_format)

                row+=1

        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)

        workbook.close()
        output.seek(0)

        filename = "student_report.xlsx"
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename={filename}'),
            ]
        )
