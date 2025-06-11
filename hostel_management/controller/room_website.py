from odoo import http
from odoo.http import request

class RoomWebsite(http.Controller):

    @http.route(['/room/<int:room_id>'], type='http', auth="public", website=True)
    def room_detail(self, room_id):
        room = request.env['room.management'].browse(room_id)
        values = {
            'room': room,
            'room_type_display': dict(room._fields['type'].selection).get(room.type),
            'room_state_display': dict(room._fields['state'].selection).get(room.state),
        }
        return request.render("hostel_management.room_detail_template", values)