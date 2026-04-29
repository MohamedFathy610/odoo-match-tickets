# models/models.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError  # استدعاء مكتبة الأخطاء عشان القيود تشتغل


# ==========================================
# 1. الموديلات الأساسية الخاصة بك
# ==========================================

class MatchUser(models.Model):
    _name = 'match.user'
    _description = 'User'

    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email', required=True)
    phone_number = fields.Char(string='Phone Number', required=True)
    password = fields.Char(string='Password', required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string='Status', default='draft')

    booking_ids = fields.One2many('match.booking', 'user_id', string='Bookings')
    credit_card_ids = fields.One2many('match.credit_card', 'user_id', string='Credit Cards')

    def action_confirm_user(self):
        for record in self:
            record.state = 'confirmed'


class MatchTicket(models.Model):
    _name = 'match.ticket'
    _description = 'Ticket'

    ticket_id = fields.Char(string='Ticket ID', required=True)
    destination = fields.Char(string='Destination', required=True)
    departure_time = fields.Datetime(string='Departure Time')

    price = fields.Float(string='Price', required=True, default=100.0)
    is_available = fields.Boolean(string='Is Available', default=True)

    # حقل الـ ISBN الجديد
    isbn = fields.Char(string='ISBN')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string='Status', default='draft')

    booking_ids = fields.One2many('match.booking', 'ticket_id', string='Match Bookings')

    # ==========================================
    # SQL Constraint: لمنع تكرار الـ ISBN في الداتابيز
    # ==========================================
    _sql_constraints = [
        ('isbn_unique', 'UNIQUE(isbn)', 'This ISBN already exists! ISBN must be unique.')
    ]

    # ==========================================
    # API Constraint: للتحقق من أن الرقم يتكون من 10 أو 13 رقم فقط
    # ==========================================
    @api.constrains('isbn')
    def _check_isbn_format(self):
        for record in self:
            if record.isbn:
                # التأكد من عدم وجود حروف
                if not record.isbn.isdigit():
                    raise ValidationError("The ISBN must contain ONLY numbers!")
                # التأكد من طول الرقم
                if len(record.isbn) not in [10, 13]:
                    raise ValidationError("The ISBN must be exactly 10 or 13 digits long!")

    # ==========================================
    # دالة الزرار لمراجعة الـ ISBN وعرض رسالة نجاح
    # ==========================================
    def action_check_isbn_manually(self):
        for record in self:
            if not record.isbn:
                raise ValidationError("Please enter an ISBN first!")

            if record.isbn.isdigit() and len(record.isbn) in [10, 13]:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success Validation',
                        'message': f'The ISBN ({record.isbn}) is perfectly valid!',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise ValidationError("Invalid ISBN! Make sure it contains 10 or 13 digits only.")

    def action_confirm_ticket(self):
        for record in self:
            record.state = 'confirmed'


class MatchBooking(models.Model):
    _name = 'match.booking'
    _description = 'Booking'

    booking_id = fields.Char(string='Booking ID', required=True)

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

        return {
            'name': 'Make Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'match.payment',
            'view_mode': 'form',
            'context': {'default_booking_id': self.id},
            'target': 'current',
        }


class MatchCreditCard(models.Model):
    _name = 'match.credit_card'
    _description = 'Credit Card'

    user_id = fields.Many2one('match.user', string='Owner', ondelete='cascade')
    card_number = fields.Char(string='Card Number', required=True)
    card_holder = fields.Char(string='Card Holder', required=True)
    expiry_date = fields.Char(string='Expiry Date')
    cvv = fields.Char(string='CVV')


class MatchPayment(models.Model):
    _name = 'match.payment'
    _description = 'Payment'

    payment_id = fields.Char(string='Payment ID', required=True)
    booking_id = fields.Many2one('match.booking', string='Booking', required=True)

    user_id = fields.Many2one(related='booking_id.user_id', string='Customer', store=True)

    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card')
    ], string='Payment Method', default='cash', required=True)

    credit_card_id = fields.Many2one('match.credit_card', string='Credit Card')

    discount_percentage = fields.Float(string='Discount (%)', default=10.0)
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
                base_price = record.booking_id.ticket_id.price
                discount_amount = base_price * (record.discount_percentage / 100.0)
                record.amount = base_price - discount_amount
            else:
                record.amount = 0.0

    def action_confirm_payment(self):
        for record in self:
            record.state = 'paid'


# ==========================================
# 2. أكواد الوراثة المضافة (التطبيقات الأربعة)
# ==========================================

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    is_match_fan = fields.Boolean(string='Is a Match Fan?', default=False)
    favorite_team = fields.Char(string='Favorite Team')


class MatchTicketExtension(models.Model):
    _inherit = 'match.ticket'

    barcode = fields.Char(string='Ticket Barcode')


class MatchTicketVIP(models.Model):
    _name = 'match.ticket.vip'
    _inherit = 'match.ticket'
    _description = 'VIP Ticket'

    vip_lounge_access = fields.Boolean(string='VIP Lounge Access', default=True)
    extra_services = fields.Char(string='Extra Services (Meals, Drinks)')


class MatchAgent(models.Model):
    _name = 'match.agent'
    _description = 'Match Agent'
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    agent_code = fields.Char(string='Agent Code', required=True)
    shift = fields.Selection([('morning', 'Morning'), ('night', 'Night')], string='Shift')