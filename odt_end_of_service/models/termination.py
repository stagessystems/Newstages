# -*- coding: utf-8 -*-
from odoo import exceptions, models, fields, api, _
from datetime import datetime
from .. import utils
from odoo.exceptions import UserError, ValidationError


class Termination(models.Model):
    _name = 'hr.termination'
    _rec_name = 'termination_code'

    # @api.one
    @api.depends('type_of_termination','period_in_years')
    def _compute_total_deserve(self):
        for termination in self:
            termination.total_deserve = 0
            print("===========vkdflvdmfvlkmvdlkf")
            total = termination.contract_id.wage
            total_five_years = termination.contract_id.wage

            if termination.type_of_termination == 'type1' or termination.type_of_termination == 'type2':
                if termination.period_in_years < 1:
                    termination.deserve_salary_amount = 0
                    termination.total_deserve = 0

                elif termination.period_in_years >= 1 and termination.period_in_years < 7:
                    final_total = (total * termination.period_in_years) / 2
                    termination.total_deserve = (final_total + termination.deserve_salary_amount)
                else:
                    total_five_years /= 2
                    total_five_years = (total_five_years * 5)
                    total_above_five_years = total * (termination.period_in_years - 5)
                    final_total = total_above_five_years + total_five_years
                    termination.total_deserve = (final_total + termination.deserve_salary_amount)

            elif termination.type_of_termination == 'type3':
                termination.deserve_salary_amount = 0
                termination.total_deserve = 0

            elif termination.type_of_termination == 'type4':
                if termination.period_in_years < 2:
                    termination.deserve_salary_amount = 0
                    termination.total_deserve = 0

                elif termination.period_in_years >= 2 and termination.period_in_years < 5:
                    total /= 2
                    final_total = (total * termination.period_in_years)
                    termination.total_deserve = (final_total + termination.deserve_salary_amount) / 3
                elif termination.period_in_years >= 5 and termination.period_in_years < 10:
                    total_five_years /= 2
                    total_five_years = (total_five_years * 5)
                    total_above_five_years = total * (termination.period_in_years - 5)
                    final_total = total_above_five_years + total_five_years
                    termination.total_deserve = (final_total + termination.deserve_salary_amount) * 2 / 3
                else:
                    total_five_years /= 2
                    total_five_years = (total_five_years * 5)
                    total_above_five_years = total * (termination.period_in_years - 5)
                    final_total = total_above_five_years + total_five_years
                    termination.total_deserve = (final_total + termination.deserve_salary_amount)

    # @api.multi
    def get_contracts(self):
        contract_obj = self.env['hr.contract']
        contract_ids = []
        for termination in self:
            date_to = termination.job_ending_date
            date_from = termination.employee_id.contract_id.date_start
            employee = termination.employee_id
            clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
            # OR if it starts between the given dates
            clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
            # OR if it starts before the date_from and finish after the date_end (or never finish)
            clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False),
                        ('date_end', '>=', date_to)]
            clause_final = [('employee_id', '=', employee.id), '|', '|'] + clause_1 + clause_2 + clause_3
            contract_ids = contract_obj.search(clause_final)
        return contract_ids

    # @api.multi
    def calculate_vacation(self):
        holiday_obj = self.env['hr.holidays']
        holiday_records = holiday_obj.search([('employee_id', '=', self.employee_id.id),
                                              ('state', '=', 'validate'),
                                              ('type', '=', 'remove')])
        total_leave = 0
        total_leave_taken = 0
        if holiday_records:
            for holiday in holiday_records:
                total_leave_taken += holiday.number_of_days_temp
        if total_leave > total_leave_taken:
            return total_leave - total_leave_taken
        else:
            return 0

    # @api.multi
    def calculate_salary(self):
        total_salary = 0.0

        class BrowsableObject(object):
            def __init__(self, employee_id, dict):
                self.employee_id = employee_id
                self.dict = dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        if self.eos_type_id and self.contract_id:
            if self.eos_type_id.salary_line_ids:
                rules_dict = {}
                obj_rule = self.env['hr.salary.rule']
                blacklist = []
                categories = BrowsableObject(self.employee_id.id, {})
                rules = BrowsableObject(self.employee_id.id, rules_dict)
                baselocaldict = {'categories': categories, 'rules': rules}
                employee = self.employee_id
                localdict = dict(baselocaldict, employee=employee, contract=self.contract_id)
                for line in self.eos_type_id.salary_line_ids:
                    localdict['result'] = None
                    localdict['result_qty'] = 1.0
                    localdict['result_rate'] = 100
                    # check if the rule can be applied
                    if obj_rule.browse(line.salary_rule_id.id).satisfy_condition(localdict) \
                            and line.salary_rule_id.id not in blacklist:
                        # compute the amount of the rule
                        amount, qty, rate = obj_rule.browse(line.salary_rule_id.id).compute_rule(localdict)
                        tot_rule = amount * qty * rate / 100.0
                        total_salary += (tot_rule * line.percentage) / 100
                    else:
                        # blacklist this rule and its children
                        blacklist += [id for id, seq in line.salary_rule_id._recursive_search_of_rules()]

        elif self.contract_id:
            total_salary = self.contract_id.wage

        return total_salary

    termination_code = fields.Char('Termination NO', readonly=True, states={'draft': [('readonly', False)]},
                                   default='Termination')
    date = fields.Date('Application Date', readonly=True, states={'draft': [('readonly', False)]},
                       default=fields.Date.today())
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, readonly=True,
                                  states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', 'Contract', required=True, readonly=True,
                                  states={'draft': [('readonly', False)]})
    job_id = fields.Many2one('hr.job', 'Job Title', readonly=True, states={'draft': [('readonly', False)]})
    job_ending_date = fields.Date('Job Ending Date', required=True, readonly=True,
                                  states={'draft': [('readonly', False)]}, defualt=fields.Date.today())
    hire_date = fields.Date('Hire Date', readonly=True, required=True, states={'draft': [('readonly', False)]})
    approved_by = fields.Many2one('res.users', 'Approved By', readonly=True, states={'draft': [('readonly', False)]})
    approval_date = fields.Date('Approval Date', readonly=True, states={'draft': [('readonly', False)]})
    # loan_value = fields.Float('Loan Value', readonly=True, states={'draft': [('readonly', False)]})
    total_deserve = fields.Float('Total Deserve', compute='_compute_total_deserve')
    eos_type_id = fields.Many2one('end.of.service.type', 'End of Service Type', readonly=True,
                                  states={'draft': [('readonly', False)]})
    from_years = fields.Float('From Years', readonly=True, states={'draft': [('readonly', False)]})
    to_years = fields.Float('To Years', readonly=True, states={'draft': [('readonly', False)]})
    basic_salary = fields.Float('Basic Salary', readonly=True, states={'draft': [('readonly', False)]})
    min_months = fields.Float('Min Months', readonly=True, states={'draft': [('readonly', False)]})
    working_period = fields.Float('Period in Months', readonly=True, states={'draft': [('readonly', False)]})
    period_in_years = fields.Float('Period in Years', readonly=True, states={'draft': [('readonly', False)]})
    termination_eos_lines = fields.One2many('hr.termination.eos.line', 'termination_id', 'End of Service Calc',
                                            readonly=True, states={'draft': [('readonly', False)]})
    vacation_days = fields.Float('Vacation Days', readonly=True, states={'draft': [('readonly', False)]})
    salary_amount = fields.Float('Salary Amount', readonly=True, states={'draft': [('readonly', False)]})
    deserve_salary_amount = fields.Float('Deserve Salary Amount', readonly=True,
                                         states={'draft': [('readonly', False)]})
    type_of_termination = fields.Selection([('type1', 'انتهاء العقد او باتفاق الطرفين'),
                                            ('type2', 'فسخ العقد من قبل صاحب العمل'),
                                            ('type3',
                                             'فسخ العقد من قبل صاحب العمل طبقا للمادة 80'),
                                            ('type4', 'استقالة العامل')], _('سبب انتهاء العلاقة'),
                                           required=True)
    state = fields.Selection([('draft', _('Draft')),
                              ('cancel', _('Cancelled')),
                              ('approved', _('Approved'))], _('Status'), readonly=True, copy=False, default='draft',
                             help=_("Gives the status of the Termination"), select=True)
    input_line_ids = fields.One2many('termination.eos.input', 'termination_id', 'Input Lines')

    @api.model
    def create(self, vals):
        termination_code = self.env['ir.sequence'].get('hr.termination.code')
        vals['termination_code'] = termination_code
        return super(Termination, self).create(vals)

    @api.onchange('employee_id')
    def onchange_employee_id(self):

        if self.employee_id:
            vals = {'domain': {'contract_id': False}}
            self.job_id = self.employee_id.job_id.id
            self.hire_date = self.employee_id.contract_id.date_start
            remaining_vacation = self.employee_id.remaining_leaves
            self.vacation_days = remaining_vacation
            contracts = self.get_contracts()
            li = []
            for i in contracts:
                li.append(i.id)
                vals['domain'].update({'contract_id': [('id', 'in', li)]})
            return vals

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if self.contract_id:
            salary = self.calculate_salary()
            self.salary_amount = salary
            self.basic_salary = salary
            remaining_vacation = self.employee_id.remaining_leaves
            self.vacation_days = remaining_vacation
            self.deserve_salary_amount = (self.contract_id.wage / 30) * remaining_vacation

    @api.onchange('vacation_days')
    def _onchange_vacation(self):
        if self.vacation_days:
            self.deserve_salary_amount = (self.salary_amount / 30) * self.vacation_days

    @api.onchange('job_ending_date', 'hire_date')
    def _onchange_dates(self):
        if self.job_ending_date and self.hire_date:
            start_date = datetime.strptime(str(self.hire_date), '%Y-%m-%d')
            end_date = datetime.strptime(str(self.job_ending_date), '%Y-%m-%d')
            print(str(end_date)+"=========")
            months = utils.months_between(start_date, end_date)
            years = utils.years_between(start_date, end_date)
            self.working_period = months
            self.period_in_years = years

    # @api.multi
    @api.onchange('eos_type_id', 'basic_salary', 'working_period')
    def _onchange_eos_type_id(self):
        if self.eos_type_id:
            entries = []
            period = self.working_period
            input_obj = self.env['termination.eos.input']
            hr_payslip_obj = self.env['hr.payslip']
            self.min_months = self.eos_type_id.minimum_months
            # old_input_ids = input_obj.search([('payslip_id', '=', self.ids[0])]) or False
            if self.input_line_ids:
                self.unlink()

            input_line_ids = hr_payslip_obj.get_inputs([self.contract_id.id], self.hire_date, self.job_ending_date)
            salary = self.calculate_salary()
            self.salary_amount = salary
            self.basic_salary = salary
            end_period = 0.0
            for line in self.eos_type_id.line_ids:

                if period >= line.from_month:
                    if period >= line.to_month:
                        end_period = line.to_month
                    else:
                        end_period = period
                    data = {
                        'level': line.level,
                        'from_month': line.from_month,
                        'to_month': end_period,
                        'value': self.basic_salary * line.value * ((end_period - line.from_month) + 1) / 12
                    }
                else:
                    if line.from_month > period:
                        continue
                    data = {
                        'level': line.level,
                        'from_month': end_period and end_period or line.from_month,
                        'to_month': line.to_month,
                        'value': 0.00
                    }
                entries.append((0, 0, data))
            self.termination_eos_lines = False
            self.termination_eos_lines = entries

    # @api.multi
    def button_approve(self):
        self.approved_by = self.env.user.id
        self.approval_date = fields.Date.today()
        self.state = 'approved'
        self.contract_id.end_of_service = self.contract_id.date_end
        self.contract_id.date_end = self.approval_date
        self.contract_id.is_terminated = True

    # @api.multi
    def button_cancel(self):
        self.state = 'cancel'

    # @api.multi
    def unlink(self):
        for termination in self:
            if termination.state not in ['draft', 'cancel']:
                raise UserError(_('You cannot delete a termination document  which is not draft or cancelled!'))
                # raise exceptions.except_orm(_('Warning!'), _('You cannot delete a termination document'
                                                            #  ' which is not draft or cancelled!'))
        return super(Termination, self).unlink()


class TerminationEOSLines(models.Model):
    _name = 'hr.termination.eos.line'

    level = fields.Char('Level')
    from_month = fields.Float('From(Months)')
    to_month = fields.Float('To(Months)')
    value = fields.Float('Calculated Value')
    termination_id = fields.Many2one('hr.termination', ondelete='cascade')


class HrContract(models.Model):
    _inherit = "hr.contract"

    end_of_service = fields.Date('Original End Date')
    is_terminated = fields.Boolean('Terminated')


class termination_eos_input(models.Model):
    '''
    Payslip Input
    '''

    _order = 'termination_id, sequence'

    _name = 'termination.eos.input'
    _description = 'termination Input'
    name = fields.Char('Description', required=True)
    termination_id = fields.Many2one('hr.termination', ondelete='cascade')
    sequence = fields.Integer('Sequence', required=True, select=True, default=10)
    code = fields.Char('Code', size=52, required=True, help="The code that can be used in the salary rules")
    amount = fields.Float('Amount',
                          help="It is used in computation. For e.g. A rule for sales having 1% commission of basic salary for per product can defined in expression like result = inputs.SALEURO.amount * contract.wage*0.01.")
    contract_id = fields.Many2one('hr.contract', 'Contract', required=True,
                                  help="The contract for which applied this input")
