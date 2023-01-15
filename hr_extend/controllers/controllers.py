# -*- coding: utf-8 -*-
# from odoo import http


# class HrExtend(http.Controller):
#     @http.route('/hr_extend/hr_extend', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_extend/hr_extend/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_extend.listing', {
#             'root': '/hr_extend/hr_extend',
#             'objects': http.request.env['hr_extend.hr_extend'].search([]),
#         })

#     @http.route('/hr_extend/hr_extend/objects/<model("hr_extend.hr_extend"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_extend.object', {
#             'object': obj
#         })
