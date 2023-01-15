# -*- coding: utf-8 -*-
# from odoo import http


# class PoExtend(http.Controller):
#     @http.route('/po_extend/po_extend/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/po_extend/po_extend/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('po_extend.listing', {
#             'root': '/po_extend/po_extend',
#             'objects': http.request.env['po_extend.po_extend'].search([]),
#         })

#     @http.route('/po_extend/po_extend/objects/<model("po_extend.po_extend"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('po_extend.object', {
#             'object': obj
#         })
