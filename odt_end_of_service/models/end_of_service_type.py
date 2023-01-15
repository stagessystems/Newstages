from odoo import models, fields, api, _


class EndOfServiceType(models.Model):
    _name = 'end.of.service.type'

    name = fields.Char('Name')
    code = fields.Char('Code', required=True)
    minimum_months = fields.Integer('Minimum Months', default=1)
    from_year = fields.Date('From Year')
    to_year = fields.Date('To Year')
    line_ids = fields.One2many('end.of.service.type.line', 'eos_type_id')
    salary_line_ids = fields.One2many('end.of.service.salary.items', 'eos_type_id')


class EndOfServiceTypeLine(models.Model):
    _name = 'end.of.service.type.line'

    level = fields.Char('Level')
    from_month = fields.Float('From(Months)')
    to_month = fields.Float('To(Months)')
    value = fields.Float('Value')
    eos_type_id = fields.Many2one('end.of.service.type', ondelete='cascade')


class EndOfServiceSalaryItems(models.Model):
    _name = 'end.of.service.salary.items'

    level = fields.Char('Level')
    salary_rule_id = fields.Many2one('hr.salary.rule', 'Name')
    percentage = fields.Float('Percentage', default=100)
    eos_type_id = fields.Many2one('end.of.service.type', ondelete='cascade')