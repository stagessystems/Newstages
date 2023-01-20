# -*- coding: utf-8 -*-
import logging
from odoo import http
_logger = logging.getLogger(__name__)


class RfqControlCstm(http.Controller):

    # @http.route('/xlsx_reports', type='http', auth='user', methods=['POST'], csrf=False)
    @http.route(['/rfq_control_custom'], type='http', auth='public', csrf=False)
    def index(self, **kw):

        _logger.info('\n\n\n\nHELLO, WORLD')
        return "Hello, world"

    @http.route('/rfq_control_custom/rfq_control_custom/objects', auth='none')
    def list(self, **kw):
        return http.request.render('rfq_control_custom.listing', {
            'root': '/rfq_control_custom/rfq_control_custom',
            'objects': http.request.env['rfq_control_custom.rfq_control_custom'].search([]),
        })

#     @http.route('/rfq_control_custom/rfq_control_custom/objects/<model("rfq_control_custom.rfq_control_custom"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rfq_control_custom.object', {
#             'object': obj
#         })
