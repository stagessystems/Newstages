# -*- coding: utf-8 -*-
# from odoo import http


# class VacationSettlement(http.Controller):
#     @http.route('/vacation_settlement/vacation_settlement/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/vacation_settlement/vacation_settlement/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('vacation_settlement.listing', {
#             'root': '/vacation_settlement/vacation_settlement',
#             'objects': http.request.env['vacation_settlement.vacation_settlement'].search([]),
#         })

#     @http.route('/vacation_settlement/vacation_settlement/objects/<model("vacation_settlement.vacation_settlement"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('vacation_settlement.object', {
#             'object': obj
#         })
