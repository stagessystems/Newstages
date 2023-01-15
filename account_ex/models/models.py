# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAnalyticAccountInh(models.Model):
    _inherit = 'account.analytic.account'

    parent_id = fields.Many2one('account.analytic.account',domain="[('company_id','=',company_id)]")
#     _description = 'account_ex.account_ex'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
