from odoo import models, fields, api
from odoo.exceptions import ValidationError
import os
import re

EGYPTIAN_TEAMS = [
    ('Al Ahly', 'Al Ahly'), ('Zamalek SC', 'Zamalek SC'), ('Al Ittihad', 'Al Ittihad'),
    ('Smouha SC', 'Smouha SC'), ('Aswan SC', 'Aswan SC'), ('Al Aluminium', 'Al Aluminium'),
    ('Al Masry', 'Al Masry'), ('Ismaily SC', 'Ismaily SC'), ('El Gouna FC', 'El Gouna FC'),
    ('ZED FC', 'ZED FC'), ('Pyramids FC', 'Pyramids FC'), ('Pharco FC', 'Pharco FC'),
    ('Suez SC', 'Suez SC'), ('Petrojet', 'Petrojet'), ('Wadi Degla', 'Wadi Degla'),
    ('Enppi', 'Enppi'), ('Ghazl El Mahalla', 'Ghazl El Mahalla'),
    ('Baladiyat El Mahalla', 'Baladiyat El Mahalla'), ('Ceramica Cleopatra', 'Ceramica Cleopatra'),
    ('National Bank of Egypt', 'National Bank of Egypt'),
]

TEAM_STADIUMS = {
    'Al Ahly': 'Cairo Stadium', 'Zamalek SC': 'Cairo Stadium', 'Al Ittihad': 'Alexandria Stadium',
    'Smouha SC': 'Alexandria Stadium', 'Aswan SC': 'Aswan Stadium', 'Al Aluminium': 'Nagaa Hammadi Stadium',
    'Al Masry': 'Borg El Arab', 'Ismaily SC': 'Ismailia Stadium', 'El Gouna FC': 'Khaled Bichara Stadium',
    'ZED FC': 'Cairo Stadium', 'Pyramids FC': '30 June Stadium', 'Pharco FC': 'Borg El Arab',
    'Suez SC': 'Suez Stadium', 'Petrojet': 'Suez Stadium', 'Wadi Degla': 'Al Salam Stadium',
    'Enppi': 'Petrosport Stadium', 'Ghazl El Mahalla': 'El Mahalla Stadium',
    'Baladiyat El Mahalla': 'El Mahalla Stadium', 'Ceramica Cleopatra': 'Arab Contractors Stadium',
    'National Bank of Egypt': 'Cairo Stadium',
}


class MatchUser(models.Model):
    _name = 'match.user'
    _description = 'User'

    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email', required=True)
    phone_number = fields.Char(string='Phone Number', required=True)
    password = fields.Char(string='Password', required=True)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], string='Status', default='draft')
    booking_ids = fields.One2many('match.booking', 'user_id', string='Bookings')
    credit_card_ids = fields.One2many('match.credit_card', 'user_id', string='Credit Cards')

    _sql_constraints = [
        ('email_unique', 'unique(email)', 'عذراً! هذا البريد الإلكتروني مسجل بالفعل لمستخدم آخر.'),
        ('phone_unique', 'unique(phone_number)', 'عذراً! رقم الهاتف هذا مسجل بالفعل لمستخدم آخر.')
    ]

    @api.constrains('email')
    def _check_email_format(self):
        for record in self:
            if record.email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', record.email):
                raise ValidationError("عذراً! يرجى إدخال بريد إلكتروني صحيح (مثال: name@example.com).")

    @api.constrains('phone_number')
    def _check_phone_number(self):
        for record in self:
            if record.phone_number:
                if not record.phone_number.isdigit():
                    raise ValidationError("عذراً! يجب أن يحتوي رقم الهاتف على أرقام فقط دون حروف أو رموز.")
                if len(record.phone_number) != 11:
                    raise ValidationError("عذراً! يجب أن يتكون رقم الهاتف من 11 رقماً بالضبط.")

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if record.name and not re.match(r'^[A-Za-z\u0600-\u06FF\s]+$', record.name):
                raise ValidationError("عذراً! يجب أن يحتوي الاسم على حروف فقط (دون أرقام أو رموز).")

    @api.constrains('password')
    def _check_password_length(self):
        for record in self:
            if record.password and len(record.password) < 6:
                raise ValidationError("عذراً! يجب أن تتكون كلمة المرور من 6 أحرف أو أرقام على الأقل.")

    def action_confirm_user(self):
        for record in self: record.state = 'confirmed'


class MatchTicket(models.Model):
    _name = 'match.ticket'
    _description = 'Ticket'
    _rec_name = 'match_name'

    ticket_id = fields.Char(string='Ticket ID', required=True, copy=False, readonly=True, default='New')
    home_team = fields.Selection(EGYPTIAN_TEAMS, string='Home Team', required=True)
    away_team = fields.Selection(EGYPTIAN_TEAMS, string='Away Team', required=True)
    match_name = fields.Char(string='Match Name', compute='_compute_match_name', store=True)
    destination = fields.Char(string='Stadium / Destination', required=True)
    departure_time = fields.Datetime(string='Match Time', required=True)
    price = fields.Float(string='Price', required=True, default=100.0)
    is_available = fields.Boolean(string='Is Available', default=True)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], string='Status', default='draft')
    booking_ids = fields.One2many('match.booking', 'ticket_id', string='Match Bookings')

    @api.onchange('home_team')
    def _onchange_home_team_stadium(self):
        if self.home_team: self.destination = TEAM_STADIUMS.get(self.home_team, 'TBD Stadium')

    @api.constrains('home_team', 'away_team')
    def _check_different_teams(self):
        for record in self:
            if record.home_team and record.away_team and record.home_team == record.away_team:
                raise ValidationError("عذراً! لا يمكن أن يلعب الفريق ضد نفسه. يرجى اختيار فريقين مختلفين.")

    @api.constrains('departure_time')
    def _check_future_date(self):
        for record in self:
            if record.departure_time and record.departure_time <= fields.Datetime.now():
                raise ValidationError("عذراً! لا يمكن تعيين موعد مباراة في الماضي. يرجى اختيار تاريخ مستقبلي.")

    @api.depends('home_team', 'away_team')
    def _compute_match_name(self):
        for record in self:
            record.match_name = f"{record.home_team} VS {record.away_team}" if record.home_team and record.away_team else "TBD"

        # قيد منع تضارب المواعيد في نفس الاستاد
        @api.constrains('destination', 'departure_time')
        def _check_stadium_conflict(self):
            for record in self:
                if record.destination and record.departure_time:
                    # البحث عن أي ماتش آخر في نفس الاستاد ونفس الوقت
                    conflict = self.search([
                        ('id', '!=', record.id),
                        ('destination', '=', record.destination),
                        ('departure_time', '=', record.departure_time)
                    ])
                    if conflict:
                        raise ValidationError(
                            f"عذراً! لا يمكن تسجيل المباراة. يوجد تضارب في المواعيد: "
                            f"استاد ({record.destination}) مشغول بمباراة أخرى في نفس التوقيت ({record.departure_time})."
                        )

    @api.model
    def create(self, vals):
        if vals.get('ticket_id', 'New') == 'New':
            vals['ticket_id'] = self.env['ir.sequence'].next_by_code('match.ticket') or 'New'
        return super(MatchTicket, self).create(vals)

    def action_confirm_ticket(self):
        for record in self: record.state = 'confirmed'


class MatchBooking(models.Model):
    _name = 'match.booking'
    _description = 'Booking'
    _rec_name = 'booking_id'

    booking_id = fields.Char(string='Booking ID', required=True, copy=False, readonly=True, default='New')
    user_id = fields.Many2one('match.user', string='User', required=True, ondelete='cascade')
    ticket_id = fields.Many2one('match.ticket', string='Match', required=True, ondelete='cascade')

    booking_time = fields.Datetime(string='Booking Time', default=fields.Datetime.now, readonly=True)

    payment_method = fields.Selection([('cash', 'Cash'), ('credit_card', 'Credit Card')], string='Payment Method',
                                      default='cash', required=True)
    credit_card_id = fields.Many2one('match.credit_card', string='Credit Card')
    is_vip = fields.Boolean(string='Upgrade to VIP (+200 EGP)', default=False)
    vip_fee = fields.Float(string='VIP Extra Fee', default=200.0, readonly=True)
    discount_percentage = fields.Float(string='Discount (%)', compute='_compute_discount', store=True)
    total_price = fields.Float(string='Total Price', compute='_compute_total_price', store=True)
    status = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')],
                              string='Status', default='draft')

    @api.constrains('user_id')
    def _check_user_confirmed(self):
        for record in self:
            if record.user_id.state != 'confirmed':
                raise ValidationError("عذراً! لا يمكن إتمام الحجز. يجب تأكيد حساب المستخدم (Confirmed) أولاً.")

    @api.constrains('ticket_id')
    def _check_ticket_availability(self):
        for record in self:
            if record.ticket_id and not record.ticket_id.is_available:
                raise ValidationError("عذراً! لا يمكن حجز هذه التذكرة لأن الماتش غير متاح حالياً.")

    @api.depends('payment_method')
    def _compute_discount(self):
        for record in self: record.discount_percentage = 10.0 if record.payment_method == 'credit_card' else 0.0

    @api.depends('ticket_id.price', 'is_vip', 'vip_fee', 'discount_percentage')
    def _compute_total_price(self):
        for record in self:
            base_price = record.ticket_id.price if record.ticket_id else 0.0
            extra = record.vip_fee if record.is_vip else 0.0
            subtotal = base_price + extra
            record.total_price = subtotal - (subtotal * (record.discount_percentage / 100.0))

    @api.model
    def create(self, vals):
        if vals.get('booking_id', 'New') == 'New':
            vals['booking_id'] = self.env['ir.sequence'].next_by_code('match.booking') or 'New'
        return super(MatchBooking, self).create(vals)

    def action_confirm_booking(self):
        for record in self: record.status = 'confirmed'
        return {'name': 'Make Payment', 'type': 'ir.actions.act_window', 'res_model': 'match.payment',
                'view_mode': 'form', 'context': {'default_booking_id': self.id}, 'target': 'current'}

    def action_cancel_booking(self):
        for record in self: record.status = 'cancelled'

    def action_print_ticket(self):
        wk_path = r'C:\Program Files\wkhtmltopdf\bin'
        if wk_path not in os.environ['PATH']:
            os.environ['PATH'] += os.pathsep + wk_path
        return self.env.ref('odoo-match-tickets.action_report_match_booking').report_action(self)


class MatchCreditCard(models.Model):
    _name = 'match.credit_card'
    _description = 'Credit Card'

    user_id = fields.Many2one('match.user', string='Owner', ondelete='cascade', required=True)
    card_number = fields.Char(string='Card Number', required=True)
    card_holder = fields.Char(string='Card Holder', required=True)
    expiry_date = fields.Char(string='Expiry Date', required=True)
    cvv = fields.Char(string='CVV', required=True)

    @api.constrains('card_number')
    def _check_card_number(self):
        for record in self:
            if not record.card_number.isdigit() or len(record.card_number) != 16:
                raise ValidationError("عذراً! رقم البطاقة يجب أن يتكون من 16 رقماً فقط.")

    @api.constrains('card_holder')
    def _check_card_holder(self):
        for record in self:
            if not re.match(r'^[A-Za-z\u0600-\u06FF\s]+$', record.card_holder):
                raise ValidationError("عذراً! اسم حامل البطاقة يجب أن يحتوي على حروف ومسافات فقط.")

    @api.constrains('expiry_date')
    def _check_expiry_date(self):
        for record in self:
            if not re.match(r'^(0[1-9]|1[0-2])\/\d{2}$', record.expiry_date):
                raise ValidationError("عذراً! تاريخ الانتهاء يجب أن يكون بصيغة MM/YY (مثال: 12/26).")

    @api.constrains('cvv')
    def _check_cvv(self):
        for record in self:
            if not record.cvv.isdigit() or len(record.cvv) not in [3, 4]:
                raise ValidationError("عذراً! رمز الـ CVV يجب أن يتكون من 3 أو 4 أرقام فقط.")


class MatchPayment(models.Model):
    _name = 'match.payment'
    _description = 'Payment'
    _rec_name = 'payment_id'

    payment_id = fields.Char(string='Payment ID', required=True, copy=False, readonly=True, default='New')
    booking_id = fields.Many2one('match.booking', string='Booking Reference', required=True, ondelete='cascade')
    user_id = fields.Many2one(related='booking_id.user_id', string='Customer', store=True)
    payment_method = fields.Selection(related='booking_id.payment_method', store=True, string='Payment Method')
    credit_card_id = fields.Many2one(related='booking_id.credit_card_id', store=True, string='Credit Card')
    discount_percentage = fields.Float(related='booking_id.discount_percentage', store=True, string='Discount (%)')
    amount = fields.Float(related='booking_id.total_price', store=True, string='Final Amount')
    payment_time = fields.Datetime(string='Payment Time', default=fields.Datetime.now)
    state = fields.Selection([('draft', 'Draft'), ('paid', 'Paid')], string='Status', default='draft')

    @api.model
    def create(self, vals):
        if vals.get('payment_id', 'New') == 'New':
            vals['payment_id'] = self.env['ir.sequence'].next_by_code('match.payment') or 'New'
        return super(MatchPayment, self).create(vals)

    def action_confirm_payment(self):
        for record in self: record.state = 'paid'

    # الدالة دي اللي كانت ناقصة وسببت المشكلة!
    def action_print_ticket(self):
        if self.booking_id:
            wk_path = r'C:\Program Files\wkhtmltopdf\bin'
            if wk_path not in os.environ['PATH']:
                os.environ['PATH'] += os.pathsep + wk_path
            return self.env.ref('odoo-match-tickets.action_report_match_booking').report_action(self.booking_id)

    @api.constrains('payment_time', 'booking_id')
    def _check_payment_time_differs_from_match(self):
        for record in self:
            if record.payment_time and record.booking_id.ticket_id.departure_time:
                if record.payment_time.date() == record.booking_id.ticket_id.departure_time.date():
                    raise ValidationError("Security Error: Payment cannot be made on the exact same day as the match!")


# ==========================================
# 2. أكواد الوراثة
# ==========================================

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