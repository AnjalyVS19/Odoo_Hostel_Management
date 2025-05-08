from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    student_id = fields.Many2one('student', string='Student')