# models/models.py
from odoo import models, fields, api


class MatchUser(models.Model):
    _name = 'match.user'
    _description = 'User'

    # Requirement 3: Required Field
    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email', required=True)
    phone_number = fields.Char(string='Phone Number')
    password = fields.Char(string='Password')  # (في الواقع بنستخدم تشفير، بس هنمشي حسب الدياجرام)

    # Requirement 5: Relationships (1 User -> Many Bookings)
    booking_ids = fields.One2many('match.booking', 'user_id', string='Bookings')


class MatchTicket(models.Model):
    _name = 'match.ticket'
    _description = 'Ticket'

    ticket_id = fields.Char(string='Ticket ID', required=True)
    destination = fields.Char(string='Destination', required=True)
    departure_time = fields.Datetime(string='Departure Time')

    # Requirement 3: Default Value
    price = fields.Float(string='Price', required=True, default=100.0)
    is_available = fields.Boolean(string='Is Available', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string='Status', default='draft')

    # دالة زرار التأكيد
    def action_confirm_ticket(self):
        for record in self:
            record.state = 'confirmed'


class MatchBooking(models.Model):
    _name = 'match.booking'
    _description = 'Booking'

    booking_id = fields.Char(string='Booking ID', required=True)

    # Requirement 5: Relationships (Booking belongs to User & Ticket)
    user_id = fields.Many2one('match.user', string='User', required=True)
    ticket_id = fields.Many2one('match.ticket', string='Ticket', required=True)

    booking_time = fields.Datetime(string='Booking Time', default=fields.Datetime.now)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')

    def action_confirm_booking(self):
        for record in self:
            record.status = 'confirmed'

        # الكود ده هو اللي بيعمل الـ Redirect لصفحة الدفع
        return {
            'name': 'Make Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'match.payment',
            'view_mode': 'form',
            # السطر الجاي ده بياخد الحجز اللي إنت واقف فيه، ويحطه كقيمة افتراضية في شاشة الدفع
            'context': {'default_booking_id': self.id},
            'target': 'current',
        }



class MatchCreditCard(models.Model):
    _name = 'match.credit_card'
    _description = 'Credit Card'

    card_number = fields.Char(string='Card Number', required=True)
    card_holder = fields.Char(string='Card Holder', required=True)
    expiry_date = fields.Char(string='Expiry Date')
    cvv = fields.Char(string='CVV')


class MatchPayment(models.Model):
    _name = 'match.payment'
    _description = 'Payment'

    payment_id = fields.Char(string='Payment ID', required=True)

    # Relationships
    booking_id = fields.Many2one('match.booking', string='Booking', required=True)
    credit_card_id = fields.Many2one('match.credit_card', string='Credit Card')

    # حقل الخصم الجديد (افتراضي 10%)
    discount_percentage = fields.Float(string='Discount (%)', default=10.0)

    # Requirement 6: Computed Field (بيحسب المبلغ النهائي بعد الخصم)
    amount = fields.Float(string='Amount', compute='_compute_amount', store=True)

    payment_time = fields.Datetime(string='Payment Time', default=fields.Datetime.now)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
    ], string='Status', default='draft')

    @api.depends('booking_id.ticket_id.price', 'discount_percentage')
    def _compute_amount(self):
        for record in self:
            if record.booking_id and record.booking_id.ticket_id:
                # 1. السعر الأساسي من التذكرة
                base_price = record.booking_id.ticket_id.price
                # 2. حساب قيمة الخصم
                discount_amount = base_price * (record.discount_percentage / 100.0)
                # 3. السعر النهائي بعد الخصم
                record.amount = base_price - discount_amount
            else:
                record.amount = 0.0

    # دالة زرار الدفع
    def action_confirm_payment(self):
        for record in self:
            record.state = 'paid'