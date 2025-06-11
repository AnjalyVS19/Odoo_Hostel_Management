from odoo import http
from odoo.http import request

class StudentWebsite(http.Controller):
    @http.route(['/student_information'], type='http', auth="public", website=True)
    def student_form(self):
        available_rooms = request.env['room.management'].sudo().search([('state','!=','full')])
        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])

        return request.render("hostel_management.student_registration_template", {
            'rooms': available_rooms,
            'countries': countries,
            'states': states,
        })

    @http.route(['/student/submit'], type='http', auth="public", website=True, csrf=False)
    def student_submit(self, **post):
        room_id = int(post.get('room_id'))
        student_obj = request.env['student'].sudo()
        room_obj = request.env['room.management'].sudo().browse(room_id)

        email=post.get('email')
        existing_user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
        if existing_user:
            return request.render("hostel_management.student_registration_template", {
                'error_message': "A user with this email already exists.",
                'post_data': post,
                'rooms': request.env['room.management'].sudo().search([('state', '!=', 'full')]),
            })

        student_obj.create({
            'name': post.get('name'),
            'dob': post.get('dob'),
            'email': post.get('email'),
            'room_id': room_id,
        })

        total_students = student_obj.search_count([('room_id', '=', room_id)])

        if total_students >= room_obj.bed:
            room_obj.write({'state': 'full'})
        elif total_students > 0:
            room_obj.write({'state': 'partial'})
        else:
            room_obj.write({'state': 'empty'})

        return request.render("hostel_management.registration_success", {})
