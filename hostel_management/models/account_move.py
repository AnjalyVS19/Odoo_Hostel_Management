from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    student_id = fields.Many2one('student', string='Student')

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for invoice in self:
            if invoice.move_type == 'out_invoice' and invoice.student_id:
                invoice.send_invoice()
        return res

    def send_invoice(self):
        template = self.env.ref('hostel_management.mail_template_invoice_student')
        if template:
            template.send_mail(self.id, force_send=True)
                
                
                
