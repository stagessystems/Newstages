# -*- coding: utf-8 -*-
# from odoo import http


# class RfqControlCustom(http.Controller):
#     @http.route('/rfq_control_custom/rfq_control_custom', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rfq_control_custom/rfq_control_custom/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('rfq_control_custom.listing', {
#             'root': '/rfq_control_custom/rfq_control_custom',
#             'objects': http.request.env['rfq_control_custom.rfq_control_custom'].search([]),
#         })

#     @http.route('/rfq_control_custom/rfq_control_custom/objects/<model("rfq_control_custom.rfq_control_custom"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rfq_control_custom.object', {
#             'object': obj
#         })
