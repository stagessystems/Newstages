from odoo import models, fields, api


class rfq_control_custom(models.Model):
    _inherit ="crossovered.budget.lines"
    _description = 'rfq_control_custom.rfq_control_custom'

    department_id = fields.Many2one("hr.department",string="department")
    # value = fields.Integer()
    # value2 = fields.Float(compute="_value_pc", store=True)
    # description = fields.Text()

    # @api.depends('value')
    # def _value_pc(self):
    #     for record in self:
    #         record.value2 = float(record.value) / 100
