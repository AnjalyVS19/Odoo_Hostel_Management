from odoo import http
from odoo.http import request


class StudentForm(http.Controller):
    @http.route('/student', auth='public', website=True)
    def Student_details(self):
        return request.render('hostel_management.student_form_view')
