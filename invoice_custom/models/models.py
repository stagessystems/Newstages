# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class invoice_custom(models.Model):
#     _name = 'invoice_custom.invoice_custom'
#     _description = 'invoice_custom.invoice_custom'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
