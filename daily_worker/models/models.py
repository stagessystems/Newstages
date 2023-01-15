# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError


class Worker(models.Model):
    _name = 'worker'
    _description = 'worker'
    _sql_constraints = [
                     ('field_unique', 
                      'unique(id_no)',
                      'ID No should be unique!')
]
    name = fields.Many2one('res.partner')
    id_no = fields.Integer(required=True)
    group_id = fields.Many2one('worker.group')
    cost = fields.Float()
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

    def open_partner_ledger(self):
        return {
            'type': 'ir.actions.client',
            'name': _('Partner Ledger'),
            'tag': 'account_report',
            'params': {
                'options': {'partner_ids': [self.name.id]},
                'ignore_session': 'both',
            },
            'context': "{'model':'account.partner.ledger'}"
        }
    def get_attendances(self):
        return {
            'name': _('worker attendance'),
            'res_model': 'worker.attendance',
            'view_mode': 'tree,form',
            'domain' : [('worker_id','=',self.id)],
            'context': {
                'active_model': 'worker',
                'active_ids': self.ids,
            },
            'target': 'currnt',
            'type': 'ir.actions.act_window',
        }


class WorkerGroup(models.Model):
    _name = 'worker.group'
    _description = 'worker.group'
    name = fields.Char()
    journal_id = fields.Many2one('account.journal')
    code = fields.Char()
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)


class WorkerAttendance(models.Model):
    _name = 'worker.attendance'
    _description = 'worker.attendance'

    worker_id = fields.Many2one('worker')
    chick_in = fields.Datetime()
    chick_out = fields.Datetime()
    hours = fields.Float(compute='get_hours',store=True)
    cost = fields.Float(related='worker_id.cost')
    deduction = fields.Float()
    total = fields.Float()
    state = fields.Selection([('draft','Draft'),('confirm','Confirm'),('paid','Paid')],default='draft')
    move_id = fields.Many2one('account.move')
    is_paid = fields.Boolean(compute='paid_state')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.move_id.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
    # @api.depends('move_id.has_reconciled_entries')
    def paid_state(self):
        for rec in self:
            rec.is_paid = False
            if rec.move_id.has_reconciled_entries:

                rec.state = 'paid'
                rec.is_paid = True
    
    
    def confirm(self):
        if self.move_id or self.state == 'confirm':
            raise UserError('The payment already done.')

        line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0
        date = self.chick_in.date()
        debit_account_id = self.worker_id.group_id.journal_id.default_account_id
        credit_account_id = self.worker_id.name.property_account_payable_id
        journal_id = self.worker_id.group_id.journal_id
        name = _('Daily for  %s ') % (self.worker_id.name.name ) 
        move_dict = {
            'narration': name,
            'ref': name ,
            'journal_id': self.worker_id.group_id.journal_id.id,
            'date': date,
        }
        amount = self.total
        if debit_account_id:
            debit_line = (0, 0, {
                'name': name,
                # 'partner_id': self.employee_id.address_home_id.id,
                'account_id': debit_account_id.id,
                'journal_id': journal_id.id,
                'date': date,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,
            })
            line_ids.append(debit_line)
            debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

        if credit_account_id:
            credit_line = (0, 0, {
                'name': name,
                'partner_id': self.worker_id.name.id,
                'account_id': credit_account_id.id,
                'journal_id': journal_id.id,
                'date': date,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
            })
            line_ids.append(credit_line)
            credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
        move_dict['line_ids'] = line_ids
        move = self.env['account.move'].create(move_dict)
        self.write({'move_id': move,'state':'confirm'})
        move.post()
        print("-------------------")
        pass
    @api.depends('chick_in','chick_out','deduction')
    def get_hours(self):
        for rec in self:
            if rec.chick_in and rec.chick_out:
                rec.hours = abs(rec.chick_in.hour -rec.chick_out.hour)
                rec.total = rec.hours * rec.cost - rec.deduction
    # journal_id = fields.Many2one('account.move')

#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
