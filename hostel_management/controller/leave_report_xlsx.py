from odoo import http
from odoo.http import request
import io
import xlsxwriter

class StudentXlsxReportController(http.Controller):

    @http.route(['/leave_report/xlsx'], type='http')
    def generate_xlsx_report_leave(self, wizard_id=None, **kwargs):
        if not wizard_id:
            return request.not_found()

        wizard = request.env['leave.request.report.wizard'].browse(int(wizard_id))
        if not wizard.exists():
            return request.not_found()

        query = """
            SELECT
                s.name, s.id as student_ids, r.name AS room_name,
                l.leave_date, l.arrival_date, (l.arrival_date - l.leave_date) AS duration
            FROM student s
            LEFT JOIN room_management r ON s.room_id = r.id
            INNER JOIN leave_request l ON l.name_id = s.id
        """

        if wizard.student_ids and wizard.room_ids:
            query += " WHERE s.id IN %s AND r.id IN %s"
            wizard.env.cr.execute(query, (tuple(wizard.student_ids.ids), tuple(wizard.room_ids.ids)))
        elif wizard.student_ids and wizard.leave_date:
            query += " WHERE s.id IN %s AND l.leave_date = %s"
            wizard.env.cr.execute(query, (tuple(wizard.student_ids.ids), wizard.leave_date))
        elif wizard.student_ids and wizard.arrival_date:
            query += " WHERE s.id IN %s AND l.arrival_date = %s"
            wizard.env.cr.execute(query, (tuple(wizard.student_ids.ids), wizard.arrival_date))
        elif wizard.room_ids and wizard.leave_date:
            query += " WHERE r.id IN %s AND l.leave_date = %s"
            wizard.env.cr.execute(query, (tuple(wizard.room_ids.ids), wizard.leave_date))
        elif wizard.room_ids and wizard.arrival_date:
            query += " WHERE r.id IN %s AND l.arrival_date = %s"
            wizard.env.cr.execute(query, (tuple(wizard.room_ids.ids), wizard.arrival_date))
        elif wizard.leave_date and wizard.arrival_date:
            query += " WHERE l.leave_date = %s AND l.arrival_date = %s"
            wizard.env.cr.execute(query, (wizard.leave_date, wizard.arrival_date))
        elif wizard.student_ids:
            query += " WHERE s.id IN %s"
            wizard.env.cr.execute(query, (tuple(wizard.student_ids.ids),))
        elif wizard.room_ids:
            query += " WHERE r.id IN %s"
            wizard.env.cr.execute(query, (tuple(wizard.room_ids.ids),))
        elif wizard.leave_date:
            query += " WHERE l.leave_date = %s"
            wizard.env.cr.execute(query, (wizard.leave_date,))
        elif wizard.arrival_date:
            query += " WHERE l.arrival_date = %s"
            wizard.env.cr.execute(query, (wizard.arrival_date,))
        else:
            wizard.env.cr.execute(query)
        result = wizard.env.cr.dictfetchall()

        students = list(set([rec['name'] for rec in result if rec['name']]))
        rooms = list(set([rec['room_name'] for rec in result if rec['room_name']]))
        start_date = list(set([rec['leave_date'] for rec in result if rec['leave_date']]))
        arrival_date = list(set([rec['arrival_date'] for rec in result if rec['arrival_date']]))

        unique_student = students[0] if len(students) == 1 else None
        unique_room = rooms[0] if len(rooms) == 1 else None
        unique_start_date = start_date[0] if len(start_date) == 1 else None
        unique_arrival_date = arrival_date[0] if len(arrival_date) == 1 else None

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Leave Report')

        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'black',
            'valign': 'vcenter',
            'bg_color': '#E0E0E0',
            'border': 1,
            'align': 'center',
        })
        cell_format = workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
            'align': 'left',
        })
        date_format = workbook.add_format({
            'num_format': 'yyyy-mm-dd',
            'border': 1,
            'valign': 'vcenter',
            'align': 'left',
        })
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'valign': 'vcenter',
            'align': 'left',
        })
        main_title = "Leave Report"
        worksheet.merge_range(0, 0, 1, 5, main_title, workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#B7DEE8',
            'border': 1
        }))
        row = 3
        max_col = 4

        if len(result) == 1:
            headers = ['SL No', 'Student', 'Room', 'Start Date', ' Arrival Date']
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
                worksheet.write(row, col, rec['leave_date'], cell_format)
                col += 1
                worksheet.write(row, col, rec['arrival_date'], cell_format)

                row += 1
        else:
            if unique_room:
                worksheet.merge_range(row, 0, row, max_col, f"Room: {unique_room}", title_format)
                row += 2
            if unique_student:
                worksheet.merge_range(row, 0, row, max_col, f"Student: {unique_student}", title_format)
                row += 2
            if unique_start_date:
                worksheet.merge_range(row, 0, row, max_col, f"Start Date: {unique_start_date}", title_format)
                row += 2
            if unique_arrival_date:
                worksheet.merge_range(row, 0, row, max_col, f"Arrival Date: {unique_arrival_date}", title_format)
                row += 1

            headers = ['SL No']
            if not unique_student:
                headers.append('Student')
            if not unique_room:
                headers.append('Room')
            if not unique_start_date:
                headers.append('Start Date')
            if not unique_arrival_date:
                headers.append('Arrival Date')
            headers += ['Duration']

            for col, header in enumerate(headers):
                worksheet.write(row, col, header, header_format)
            row += 1

            for i, rec in enumerate(result, start=1):
                col = 0
                worksheet.write(row, col, i, cell_format)
                col += 1

                if not unique_student:
                    worksheet.write(row, col, rec['name'], cell_format)
                    col += 1
                if not unique_room:
                    worksheet.write(row, col, rec['room_name'], cell_format)
                    col += 1
                if not unique_start_date:
                    worksheet.write(row, col, rec['leave_date'], date_format)
                    col += 1
                if not unique_arrival_date:
                    worksheet.write(row, col, rec['arrival_date'], date_format)
                    col += 1
                worksheet.write(row, col, rec['duration'], cell_format)

                row += 1
        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)

        workbook.close()
        output.seek(0)

        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename=leave_report.xlsx'),
            ]
        )