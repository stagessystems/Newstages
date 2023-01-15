# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    def _compute_loan_amount(self):
        total_paid = 0.0
        for loan in self:
            for line in loan.loan_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = loan.loan_amount - total_paid
            loan.total_amount = loan.loan_amount
            loan.balance_amount = balance_amount
            loan.total_paid_amount = total_paid

    name = fields.Char(string="Loan Name", default="/", readonly=True, help="Name of the loan")
    date = fields.Date(string="Date", default=fields.Date.today(), readonly=True, help="Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="Employee")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department", help="Employee")
    installment = fields.Integer(string="No Of Installments", default=1, help="Number of installments")
    payment_date = fields.Date(string="Payment Start Date", required=True, default=fields.Date.today(), help="Date of "
                                                                                                             "the "
                                                                                                             "paymemt")
    loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.user.company_id,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, help="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position",
                                   help="Job position")
    loan_amount = fields.Float(string="Loan Amount", required=True, help="Loan amount")
    total_amount = fields.Float(string="Total Amount", store=True, readonly=True, compute='_compute_loan_amount',
                                help="Total loan amount")
    balance_amount = fields.Float(string="Balance Amount", store=True, compute='_compute_loan_amount', help="Balance amount")
    total_paid_amount = fields.Float(string="Total Paid Amount", store=True, compute='_compute_loan_amount',
                                     help="Total paid amount")
    type_id = fields.Many2one('hr.loan.type', 'Type' )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )
    journal_id = fields.Many2one('account.journal',string='Journal')
    move_id = fields.Many2one('account.move',string='Accounting Entry')

    @api.model
    def create(self, values):
        loan_count = self.env['hr.loan'].search_count(
            [('employee_id', '=', values['employee_id']), ('state', '=', 'approve'),
             ('balance_amount', '!=', 0)])
        if loan_count:
            raise ValidationError(_("The employee has already a pending installment"))
        else:
            values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
            res = super(HrLoan, self).create(values)
            return res

    def compute_installment(self):
        for loan in self:
            loan.loan_lines.unlink()
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            amount = loan.loan_amount / loan.installment
            for i in range(1, loan.installment + 1):
                self.env['hr.loan.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id})
                date_start = date_start + relativedelta(months=1)
            loan._compute_loan_amount()
        return True

    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_submit(self):
        self.write({'state': 'waiting_approval_1'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_approve(self):
        for data in self:
            if not data.loan_lines:
                raise ValidationError(_("Please Compute installment"))
            else:
                self.write({'state': 'approve'})

    def unlink(self):
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise UserError(
                    'You cannot delete a loan which is not in draft or cancelled state')
        return super(HrLoan, self).unlink()
    @api.onchange('type_id')
    def onchange_type_id(self):
        if self.type_id.installments_no != 0:
            self.installment = self.type_id.installments_no
        else:
            self.installment = 0

    def create_payment(self):
        if self.move_id:
            raise UserError('The payment already done.')

        line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0
        date = self.payment_date 
        debit_account_id = self.env['ir.config_parameter'].get_param('hr_loan.loan_account_id')
        credit_account_id = self.journal_id.default_account_id
        debit_account_id = self.env['account.account'].search([('id','=',debit_account_id)])
        name = _('Loan for  %s') % (self.employee_id.name)
        move_dict = {
            'narration': name,
            'ref': self.name,
            'journal_id': self.journal_id.id,
            'date': date,
        }
        amount = self.loan_amount
        if debit_account_id:
            debit_line = (0, 0, {
                'name': self.name,
                'partner_id': self.employee_id.address_home_id.id,
                'account_id': debit_account_id.id,
                'journal_id': self.journal_id.id,
                'date': date,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,
            })
            line_ids.append(debit_line)
            debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

        if credit_account_id:
            credit_line = (0, 0, {
                'name': self.name,
                'partner_id': self.employee_id.address_home_id.id,
                'account_id': credit_account_id.id,
                'journal_id': self.journal_id.id,
                'date': date,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
            })
            line_ids.append(credit_line)
            credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
        move_dict['line_ids'] = line_ids

        print("-----------------move_dict move_dict -----",move_dict)
        move = self.env['account.move'].create(move_dict)
        self.write({'move_id': move})
        move.post()

class InstallmentLine(models.Model):
    _name = "hr.loan.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True, help="Date of the payment")
    employee_id = fields.Many2one('hr.employee', string="Employee", help="Employee")
    amount = fields.Float(string="Amount", required=True, help="Amount")
    paid = fields.Boolean(string="Paid", help="Paid")
    loan_id = fields.Many2one('hr.loan', string="Loan Ref.", help="Loan")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.", help="Payslip")


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _compute_employee_loans(self):
        self.loan_count = self.env['hr.loan'].search_count([('employee_id', '=', self.id)])

    loan_count = fields.Integer(string="Loan Count", compute='_compute_employee_loans')
    def action_open_loan(self):
        action = self.env.ref('hr_loan.act_hr_employee_loan_request').read()[0]
        action['name'] = "Loans"
        action['domain'] = [('employee_id','=',self.id)]
        action['context'] = {'default_employee_id' : self.id}
        action['nodestroy'] = True
        return action
class HRLoanType(models.Model):
    _name = 'hr.loan.type'

    name = fields.Char()
    installments_no = fields.Integer()
    code = fields.Char()


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    loan_account_id = fields.Many2one('account.account',string='Loans account',config_parameter='hr_loan.loan_account_id')