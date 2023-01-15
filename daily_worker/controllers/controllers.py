# -*- coding: utf-8 -*-
# from odoo import http


# class DailyWorker(http.Controller):
#     @http.route('/daily_worker/daily_worker/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/daily_worker/daily_worker/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('daily_worker.listing', {
#             'root': '/daily_worker/daily_worker',
#             'objects': http.request.env['daily_worker.daily_worker'].search([]),
#         })

#     @http.route('/daily_worker/daily_worker/objects/<model("daily_worker.daily_worker"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('daily_worker.object', {
#             'object': obj
#         })
