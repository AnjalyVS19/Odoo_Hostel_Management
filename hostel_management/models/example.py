from odoo import fields, models


class Example(models.Model):
    _name = "example"
    _description = "Example"

    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', 'Partner')
    tag_ids = fields.Many2many('example.tags', string='Tags')
    line_ids = fields.One2many('example.lines','example_id')

    def action_test(self):
        print('Hi')
