from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    student_id = fields.Many2one('student', string='Student')

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        if 'state' in vals and vals['state'] == 'posted':
            for invoice in self:
                if invoice.move_type == 'out_invoice':
                    invoice.send_invoice_email()
        return res

    def send_invoice_email(self):
        template = self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)
        if template:
            for invoice in self:
                template.send_mail(invoice.id, force_send=True)
