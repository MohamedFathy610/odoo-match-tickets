from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, time, timedelta
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
        ('email_unique', 'unique(email)', 'Sorry! This email is already registered to another user.'),
        ('phone_unique', 'unique(phone_number)', 'Sorry! This phone number is already registered to another user.')
    ]

    @api.constrains('email')
    def _check_email_format(self):
        for record in self:
            if record.email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', record.email):
                raise ValidationError("Sorry! Please enter a valid email address (e.g., name@example.com).")

    @api.constrains('phone_number')
    def _check_phone_number(self):
        for record in self:
            if record.phone_number:
                if not record.phone_number.isdigit():
                    raise ValidationError("Sorry! The phone number must contain only digits, without letters or symbols.")
                if len(record.phone_number) != 11:
                    raise ValidationError("Sorry! The phone number must consist of exactly 11 digits.")

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if record.name and not re.match(r'^[A-Za-z\u0600-\u06FF\s]+$', record.name):
                raise ValidationError("Sorry! The name must contain only letters and spaces (no numbers or symbols).")

    @api.constrains('password')
    def _check_password_length(self):
        for record in self:
            if record.password and len(record.password) < 6:
                raise ValidationError("Sorry! The password must be at least 6 characters or digits long.")

    def action_confirm_user(self):
        for record in self: record.state = 'confirmed'

    def write(self, vals):
        for record in self:
            if record.state == 'confirmed' and set(vals.keys()) - {'state'}:
                raise ValidationError("Sorry! User data cannot be modified after the account has been confirmed.")
        return super(MatchUser, self).write(vals)


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


    _sql_constraints = [
        ('ticket_id_unique', 'unique(ticket_id)', 'Sorry! Ticket ID must be unique!')
    ]

    @api.onchange('home_team')
    def _onchange_home_team_stadium(self):
        if self.home_team:
            self.destination = TEAM_STADIUMS.get(self.home_team, 'TBD Stadium')

    @api.depends('home_team', 'away_team')
    def _compute_match_name(self):
        for record in self:
            record.match_name = f"{record.home_team} VS {record.away_team}" if record.home_team and record.away_team else "TBD"

    # ==========================================
    # Logical Validations
    # ==========================================

    @api.constrains('home_team', 'away_team')
    def _check_different_teams(self):
        for record in self:
            if record.home_team and record.away_team and record.home_team == record.away_team:
                raise ValidationError("Sorry! A team cannot play against itself. Please select two different teams.")

    @api.constrains('price')
    def _check_logical_price(self):
        for record in self:
            if record.price <= 0:
                raise ValidationError("Sorry! The ticket price must be a number greater than zero.")
            if record.price > 50000:
                raise ValidationError("Sorry! The price is unusually high. Please ensure you enter the correct ticket value.")

    @api.constrains('departure_time')
    def _check_future_date(self):
        for record in self:
            if record.departure_time and record.departure_time <= fields.Datetime.now():
                raise ValidationError("Sorry! A match cannot be scheduled in the past. Please choose a future date.")

    @api.constrains('departure_time', 'destination', 'home_team', 'away_team')
    def _check_logical_scheduling(self):
        for record in self:
            if not record.departure_time:
                continue

            # 1. Stadium Constraint (Only one match per day per stadium)
            match_date = record.departure_time.date()
            start_of_day = datetime.combine(match_date, time.min)
            end_of_day = datetime.combine(match_date, time.max)

            stadium_conflict = self.search([
                ('id', '!=', record.id),
                ('destination', '=', record.destination),
                ('departure_time', '>=', start_of_day),
                ('departure_time', '<=', end_of_day)
            ])
            if stadium_conflict:
                raise ValidationError(
                    f"Sorry! The stadium ({record.destination}) is already booked for another match on this day. "
                    f"A stadium cannot host more than one match per day."
                )

            # 2. Team Fatigue Constraint (Teams must have a 3-day / 72-hour rest period)
            team_buffer = timedelta(days=3)
            team_start = record.departure_time - team_buffer
            team_end = record.departure_time + team_buffer

            team_conflict = self.search([
                ('id', '!=', record.id),
                ('departure_time', '>=', team_start),
                ('departure_time', '<=', team_end),
                '|', '|', '|',
                ('home_team', '=', record.home_team),
                ('away_team', '=', record.home_team),
                ('home_team', '=', record.away_team),
                ('away_team', '=', record.away_team)
            ])
            if team_conflict:
                raise ValidationError(
                    f"Sorry! One of the teams ({record.home_team} or {record.away_team}) "
                    f"already has a match scheduled within 3 days of this date. Please allow for the required rest period."
                )

            # 3. Home and Away System Constraint (Teams can only play twice with swapped home/away sides)
            history_conflict = self.search([
                ('id', '!=', record.id),
                ('home_team', '=', record.home_team),
                ('away_team', '=', record.away_team)
            ])
            if history_conflict:
                raise ValidationError(
                    f"Sorry! The match between ({record.home_team}) as the home team and ({record.away_team}) as the away team "
                    f"has already been played. Under the home-and-away system, this exact matchup cannot be repeated unless ({record.away_team}) is the home team."
                )

    # ==========================================
    # Core Functions
    # ==========================================

    @api.model
    def create(self, vals):
        if vals.get('ticket_id', 'New') == 'New':
            vals['ticket_id'] = self.env['ir.sequence'].next_by_code('match.ticket') or 'New'
        return super(MatchTicket, self).create(vals)

    def action_confirm_ticket(self):
        for record in self:
            record.state = 'confirmed'

    def write(self, vals):
        for record in self:
            if record.state == 'confirmed' and set(vals.keys()) - {'state'}:
                raise ValidationError("Sorry! Ticket data cannot be modified after it has been confirmed.")
        return super(MatchTicket, self).write(vals)


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
    destination = fields.Char(related='ticket_id.destination', string='Stadium', readonly=True)
    _sql_constraints = [
        ('booking_id_unique', 'unique(booking_id)', 'Sorry! Booking ID must be unique!'),
        ('user_ticket_unique', 'unique(user_id, ticket_id)', 'Sorry! You have already booked a ticket for this match!')
    ]

    @api.constrains('user_id', 'ticket_id')
    def _check_user_daily_limit(self):
        for record in self:
            if not record.ticket_id or not record.user_id:
                continue

            # الحصول على تاريخ الماتش الحالي
            current_match_date = record.ticket_id.departure_time.date()

            # البحث عن حجوزات أخرى لنفس المستخدم في نفس تاريخ الماتش
            other_bookings = self.search([
                ('id', '!=', record.id),
                ('user_id', '=', record.user_id.id),
                ('status', '!=', 'cancelled')
            ])

            for b in other_bookings:
                if b.ticket_id.departure_time.date() == current_match_date:
                    raise ValidationError("Sorry! This user already has another booking on the same day.")

    @api.constrains('user_id')
    def _check_user_confirmed(self):
        for record in self:
            if record.user_id.state != 'confirmed':
                raise ValidationError("Sorry! The booking cannot be completed. The user account must be confirmed first.")

    @api.constrains('ticket_id')
    def _check_ticket_availability(self):
        for record in self:
            if record.ticket_id and not record.ticket_id.is_available:
                raise ValidationError("Sorry! This ticket cannot be booked because the match is not currently available.")

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

    def write(self, vals):
        for record in self:
            if record.status == 'confirmed' and set(vals.keys()) - {'status'}:
                raise ValidationError("Sorry! Booking data cannot be modified after it has been confirmed.")
        return super(MatchBooking, self).write(vals)


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
                raise ValidationError("Sorry! The card number must consist of exactly 16 digits.")

    @api.constrains('card_holder')
    def _check_card_holder(self):
        for record in self:
            if not re.match(r'^[A-Za-z\u0600-\u06FF\s]+$', record.card_holder):
                raise ValidationError("Sorry! The cardholder name must contain only letters and spaces.")

    @api.constrains('expiry_date')
    def _check_expiry_date(self):
        for record in self:
            if not re.match(r'^(0[1-9]|1[0-2])\/\d{2}$', record.expiry_date):
                raise ValidationError("Sorry! The expiry date must be in the format MM/YY (e.g., 12/26).")

    @api.constrains('cvv')
    def _check_cvv(self):
        for record in self:
            if not record.cvv.isdigit() or len(record.cvv) not in [3, 4]:
                raise ValidationError("Sorry! The CVV code must consist of exactly 3 or 4 digits.")


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

    _sql_constraints = [
        ('payment_id_unique', 'unique(payment_id)', 'Sorry! Payment ID must be unique!')
    ]

    @api.model
    def create(self, vals):
        if vals.get('payment_id', 'New') == 'New':
            vals['payment_id'] = self.env['ir.sequence'].next_by_code('match.payment') or 'New'
        return super(MatchPayment, self).create(vals)

    def action_confirm_payment(self):
        for record in self: record.state = 'paid'

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

    def write(self, vals):
        for record in self:
            if record.state == 'paid' and set(vals.keys()) - {'state'}:
                raise ValidationError("Sorry! Payment data cannot be modified after the transaction is completed.")
        return super(MatchPayment, self).write(vals)


# ==========================================
# 2. Inheritance Code
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