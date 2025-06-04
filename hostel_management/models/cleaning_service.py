from odoo import models, fields


class CleaningService(models.Model):
    _name = "cleaning.service"
    _description = "Cleaning"
    _rec_name = "room_id"


    room_id = fields.Many2one('room.management', string='Room', required=True)
    start_time = fields.Datetime(string="Start Time", required=True)
    cleaning_staff_id = fields.Many2one('res.users', string='Cleaning Staff', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, index=True, store=True )
    state = fields.Selection([
        ('new','New'),
        ('assigned','Assigned'),
        ('done','Done')
    ],string='Status', default='new')
    previous_state = fields.Char()

    def assign_staff(self):
        for record in self:
            record.previous_state = record.room_id.state
            record.write({
                'state': 'assigned',
                'cleaning_staff_id': self.env.user.id
            })
            if record.room_id:
                record.room_id.state = 'cleaning'

    def complete_cleaning(self):
        self.write({'state':'done'})
        if self.room_id:
            self.room_id.state = self.previous_state
            if self.previous_state == 'cleaning':
                if self.room_id.bed_booked == self.room_id.bed:
                    self.room_id.state = 'full'
                elif self.room_id.bed_booked == 0:
                    self.room_id.state = 'empty'
                else:
                    self.room_id.state = 'partial'


