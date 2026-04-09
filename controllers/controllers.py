# -*- coding: utf-8 -*-
# from odoo import http


# class MatchTicket(http.Controller):
#     @http.route('/match_ticket/match_ticket', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/match_ticket/match_ticket/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('match_ticket.listing', {
#             'root': '/match_ticket/match_ticket',
#             'objects': http.request.env['match_ticket.match_ticket'].search([]),
#         })

#     @http.route('/match_ticket/match_ticket/objects/<model("match_ticket.match_ticket"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('match_ticket.object', {
#             'object': obj
#         })

