# -*- coding: utf-8 -*-
# from odoo import http


# class Discount(http.Controller):
#     @http.route('/discount/discount/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/discount/discount/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('discount.listing', {
#             'root': '/discount/discount',
#             'objects': http.request.env['discount.discount'].search([]),
#         })

#     @http.route('/discount/discount/objects/<model("discount.discount"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('discount.object', {
#             'object': obj
#         })
