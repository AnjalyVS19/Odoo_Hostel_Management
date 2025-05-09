from odoo import  models, fields, api, _

class RoomManagement(models.Model):
    _name = "room.management"
    _description = "Room"
    _inherit = 'mail.thread'

    state = fields.Selection([
        ('empty', 'Empty'),
        ('partial', 'Partial'),
        ('full', 'Full')
    ], string='Status', default='empty')
    name = fields.Char("Room Number", default="New", copy=False, readonly=True, tracking=True, required=True)
    type = fields.Selection(string="Room Type",
                            selection=[('a/c','A/C'),
                                       ('non a/c','Non A/C')], required=True)
    bed = fields.Integer(string="Number of Beds", required=True)
    bed_booked = fields.Integer()
    company_id = fields.Many2one('res.company', copy=False,
                                 string="Company",
                                 default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  related='company_id.currency_id',
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    rent = fields.Monetary(string="Rent", required=True)
    facilities_ids = fields.Many2many('facilities', string='Facilities')
    student_ids = fields.One2many('student', 'room_id', string='Students', readonly=True)
    total_rent = fields.Monetary(string="Total Rent", compute="_compute_total_rent", store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = (self.env['ir.sequence'].sudo().
                                  next_by_code('room_management'))
        return super().create(vals_list)

    def allotted_students(self):
        if self.name == (self.env[student.room_id]):
            self.student_ids = (self.env[student.name])

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
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created_invoices.ids)],
        }
