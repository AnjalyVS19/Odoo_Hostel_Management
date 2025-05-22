from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Facilities(models.Model):
    _name = "facilities"
    _description = "Facilities"

    name = fields.Char(string="Facility", required=True)
    charge = fields.Float(string='Charge', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, index=True, store=True )

    @api.constrains('charge')
    def my_warning(self):
        if self.charge <= 0:
            raise ValidationError("Charge must be greater than 0.")