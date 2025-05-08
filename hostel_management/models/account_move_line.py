from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    student_id = fields.Many2one('student', string='Student')

