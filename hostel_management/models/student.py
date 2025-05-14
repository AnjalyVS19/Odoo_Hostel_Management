# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

class Student(models.Model):
    _name = "student"
    _description = "Student"

    student_image = fields.Image()
    name = fields.Char(string="Name", required=True)
    dob = fields.Date(string='DOB', required=True)
    room_id = fields.Many2one(comodel_name='room.management', string='Room', readonly=True)
    email = fields.Char(required=True)
    receive = fields.Boolean(string='Receive Mail')
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one('res.country.state', string="State")
    country_id = fields.Many2one('res.country', string="Country")
    sid = fields.Char("Student Id", default="New", copy=False, readonly=True)
    company_id = fields.Many2one('res.company', store=True, copy=False,
                                 string="Company",
                                 default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  related='company_id.currency_id',
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    age = fields.Char(compute='_onchange_birth_date', string='Age')
    bed = fields.Integer(required=True)
    available_rooms = fields.Char(Invisible=True)
    cleaning_room = fields.Char(Invisible=True)
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='restrict', auto_join=True, readonly=True,)
    partner = fields.Char(related='partner_id.name', string="Partner", store=True, readonly=True)
    invoice_count = fields.Integer(compute="_compute_invoice_count", string="Invoice Count")
    active = fields.Boolean(default=True, Invisible=True)
    monthly_amount = fields.Monetary(string='Monthly Amount', readonly=True, related='room_id.total_rent')
    invoice_status = fields.Selection(selection=[
        ('pending','Pending'),
        ('done','Done')
    ], string='Invoice Status', compute='_compute_pending_invoices', store=False)
    user_id = fields.Many2one('res.partner', string='Partner', ondelete='restrict', auto_join=True, readonly=True,)
    user = fields.Char(related='partner_id.name', string="Partner", store=True, readonly=True)

    @api.onchange('dob')
    def _onchange_birth_date(self):
        if self.dob:
            d1 = self.dob
            d2 = date.today()
            self.age = relativedelta(d2, d1).years

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('sid', _('New')) == _('New'):
                vals['sid'] = (self.env['ir.sequence'].
                               next_by_code('student'))
        return super().create(vals_list)

    def alot_button(self):
        self.active = True
        for student in self:
            available_room = self.env['room.management'].search([
                ('state', 'in', ['empty', 'partial']),
                ('bed', '>', 0)
            ], limit=1)

            if not available_room:
                raise UserError('No available rooms to allocate.')
            room_id = available_room
            student.room_id = room_id
            room_id.bed_booked += 1
            remaining_beds = room_id.bed - room_id.bed_booked
            if remaining_beds == 0:
                room_id.state = 'full'
            elif remaining_beds < room_id.bed:
                room_id.state = 'partial'
            else:
                room_id.state = 'empty'

    @api.depends('room_id')
    def vacate_button(self):
        for student in self:
            room = student.room_id
            if room:
                room.bed_booked -= 1
                remaining_beds = room.bed - room.bed_booked
                if remaining_beds == 0:
                    room.state = 'empty'
                elif remaining_beds < room.bed:
                    room.state = 'partial'
                else:
                    room.state = 'empty'
                    room.cleaning_request()
                student.room_id = False
        self.active = False

    def unlink(self):
        for student in self:
            leave_requests = self.env['leave.request'].search([('name', '=', student.id)])
            leave_requests.unlink()
            room = student.room_id
            if room:
                room.bed_booked -= 1
                remaining_beds = room.bed - room.bed_booked
                if remaining_beds == 0:
                    room.state = 'empty'
                elif remaining_beds < room.bed:
                    room.state = 'partial'
                else:
                    room.state = 'empty'
                student.room_id = False
        return super().unlink()

    def _compute_invoice_count(self):
        for student in self:
            student.invoice_count = self.env['account.move'].search_count([
                ('student_id', '=', student.id),
                ('move_type', '=', 'out_invoice')
            ])

    def action_view_student_invoices(self):
        invoices = self.env['account.move'].search([
            ('student_id', '=', self.id),
            ('move_type', '=', 'out_invoice')
        ])
        if len(invoices) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoice',
                'res_model': 'account.move',
                'res_id': invoices.id,
                'view_mode': 'form',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoices',
                'res_model': 'account.move',
                'domain': [('student_id', '=', self.id), ('move_type', '=', 'out_invoice')],
                'view_mode': 'list,form',
            }

    def action_create_monthly_invoice(self):
        product = self.env.ref('hostel_management.product_rent')
        for student in self:
            if not student.room_id:
                continue
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'student_id': student.id,
                'partner_id': student.partner_id.id,
                'invoice_line_ids': [(0, 0, {
                    'product_id': product.id,
                    'quantity': 1,
                    'price_unit': student.room_id.total_rent,
                    'name': 'Monthly Rent'
                })]
            })
            student._compute_invoice_count()
            return {
                'name': 'Invoice',
                'view_mode': 'list,form',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'type': 'ir.actions.act_window',
            }

    @api.depends_context('uid')
    def _compute_pending_invoices(self):
        for student in self:
            unpaid_invoices = self.env['account.move'].search([
                ('student_id', '=', student.id),
                ('move_type', '=', 'out_invoice'),
                ('payment_state', '!=', 'paid')
            ])
            student.invoice_status = 'pending' if unpaid_invoices else 'done'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            partner = self.env['res.partner'].create({
                'name': vals.get('name'),
                'email': vals.get('email'),
                'street': vals.get('street'),
                'street2': vals.get('street2'),
                'zip': vals.get('zip'),
                'city': vals.get('city'),
                'state_id': vals.get('state_id'),
                'country_id': vals.get('country_id'),
            })
            vals['partner_id'] = partner.id
            if vals.get('sid', _('New')) == _('New'):
                vals['sid'] = self.env['ir.sequence'].next_by_code('student') or _('New')
        return super().create(vals_list)

    @api.model
    def generate_monthly_invoice(self):
        students = self.search([])
        for student in students:
            if not student.partner_id:
                continue
            income_account = self.env['account.account'].search(
                [('account_type', '=', 'income')], limit=1)
            if not income_account:
                raise ValueError("No income account found. Please configure one.")
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'student_id': student.id,
                'partner_id': student.partner_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [(0, 0, {
                    'name': 'Monthly Fee',
                    'quantity': 1,
                    'price_unit': 1000,
                    'account_id': income_account.id,
                })]
            })
            invoice.action_post()
