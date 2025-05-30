from odoo import  models, fields, api, _
from odoo.api import readonly
from odoo.exceptions import UserError


class RoomManagement(models.Model):
    _name = "room.management"
    _description = "Room"
    _inherit = 'mail.thread'

    state = fields.Selection([
        ('empty', 'Empty'),
        ('partial', 'Partial'),
        ('full', 'Full'),
        ('cleaning','Cleaning')
    ], string='Status', default='empty')
    name = fields.Char("Room Number", default="New", readonly=True, tracking=True, required=True)
    type = fields.Selection(string="Room Type",
                            selection=[('a/c','A/C'),
                                       ('non a/c','Non A/C')], required=True)
    bed = fields.Integer(string="Number of Beds", required=True)
    bed_booked = fields.Integer()
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, index=True, store=True )
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  related='company_id.currency_id',
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    rent = fields.Monetary(string="Rent", required=True)
    facilities_ids = fields.Many2many('facilities', string='Facilities')
    student_ids = fields.One2many('student', 'room_id', string='Students', readonly=True)
    total_rent = fields.Monetary(string="Total Rent", compute="_compute_total_rent", store=True)
    previous_state = fields.Char()
    pending_amount = fields.Float(string='Pending Amount', currency_field='currency_id', readonly=True)
    user_id = fields.Many2one('res.users', string="Related User", default=lambda self: self.env.user, invisible=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            company = self.env.company
            if vals.get('name', _('New')) == _('New'):
                sequence_code = False
                if company.name == 'My Company (San Francisco)':
                    sequence_code = 'room.management.my.company'
                elif company.name == 'IN Company':
                    sequence_code = 'room.management.in'
                elif company.name == 'My Company (Chicago)':
                    sequence_code = 'room.management.chicago'

                if sequence_code:
                    vals['name'] = self.env['ir.sequence'].sudo().next_by_code(sequence_code) or _('New')

        return super().create(vals_list)

    def allotted_students(self):
        for room in self:
            students = self.env['student'].search([('room_id', '=', room.id)])
            room.student_ids = [(6, 0, students.ids)]

    @api.depends('rent', 'facilities_ids.charge')
    def _compute_total_rent(self):
        facility_total = sum(facility.charge for facility in self.facilities_ids)
        self.total_rent = self.rent + facility_total

    def monthly_invoice(self):
        rent_product = self.env.ref('hostel_management.product_rent')
        created_invoices = self.env['account.move']
        for room in self:
            for student in room.student_ids:
                if not student.partner_id:
                    continue
                invoice = self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'partner_id': student.partner_id.id,
                    'student_id': student.id,
                    'invoice_line_ids': [(0, 0, {
                        'product_id': rent_product.id,
                        'quantity': 1,
                        'price_unit': room.total_rent,
                    })]
                })
                created_invoices += invoice

            for room in self:
                total = 0.0
                for student in room.student_ids:
                    invoices = self.env['account.move'].search([
                        ('student_id', '=', student.id),
                        ('move_type', '=', 'out_invoice'),
                        ('payment_state', '!=', 'paid')
                    ])
                    total += sum(inv.amount_residual for inv in invoices)
                room.pending_amount = total

        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created_invoices.ids)],
        }


    def cleaning_request(self):
        self.previous_state = self.state
        CleaningService = self.env['cleaning.service']
        for room in self:
            if room.state == 'empty':
                CleaningService.create({
                    'room_id': room.id,
                    'start_time': fields.Datetime.now(),
                    'state': 'new',
                })
                room.state = 'cleaning'
            else:
                raise UserError("Cleaning request can only be created if the room is empty.")

    @api.onchange('bed')
    def onchange_bed(self):
        for room in self:
            room.update_room_state()

    def update_room_state(self):
        for room in self:
            if room.bed_booked >= room.bed:
                room.state = 'full'
            elif 0 < room.bed_booked < room.bed:
                room.state = 'partial'
            elif room.bed_booked == 0:
                room.state = 'empty'



