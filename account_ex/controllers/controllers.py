# -*- coding: utf-8 -*-
# from odoo import http


# class AccountEx(http.Controller):
#     @http.route('/account_ex/account_ex/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_ex/account_ex/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_ex.listing', {
#             'root': '/account_ex/account_ex',
#             'objects': http.request.env['account_ex.account_ex'].search([]),
#         })

#     @http.route('/account_ex/account_ex/objects/<model("account_ex.account_ex"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_ex.object', {
#             'object': obj
#         })
