# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from num2words import num2words
from datetime import datetime
import logging 
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class HREMployeeBaseIng(models.AbstractModel):
    _inherit = "hr.employee.base"
    effective_dates_count = fields.Integer(string='Effective Dates Count', compute='get_effective_dates_count')

    def get_effective_dates_count(self):
        count = self.env['hr.effective.date'].search_count([('employee_id', '=', self.id)])
        self.effective_dates_count = count
class HREmployee(models.Model):
    _inherit = 'hr.employee'
 
    annual_leave_days = fields.Selection(
        string='Annual leave Days',
        selection=[('21', '21 Days'),
                   ('30', '30 Days'), ],
        required=False,default='21' )

    effective_dates_count = fields.Integer(string='Effective Dates Count', compute='get_effective_dates_count')
    last_effective_date = fields.Date(
        string='Last Effective Date',
        required=False, compute='_compute_last_effective_date', store=True)
    effective_date_ids = fields.One2many(
        comodel_name='hr.effective.date',
        inverse_name='employee_id',
        string='Effective Dates',
        required=False)

    def open_effective_dates(self):
        return {
            'name': _('Effective Dates'),
            'domain': [('employee_id', '=', self.id)],
            'res_model': 'hr.effective.date',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_effective_dates_count(self):
        count = self.env['hr.effective.date'].search_count([('employee_id', '=', self.id)])
        self.effective_dates_count = count

    @api.depends('effective_date_ids')
    def _compute_last_effective_date(self):
        for record in self:
            dates = []
            for line in record['effective_date_ids']:
                if line.start_date:
                    dates.append(line.start_date)
            if dates:
                record.last_effective_date = max(dates)
                print("=========================", dates)
class HrEmployeePublicInherit(models.Model):
    _inherit = 'hr.employee.public'
    effective_dates_count = fields.Integer(readonly=True)
    last_effective_date = fields.Date(readonly=True)
    effective_date_ids = fields.One2many(readonly=True)
    # annual_leave_days = fields.Selection(readonly=True)

class VacationSettlement(models.Model):
    _inherit = 'hr.leave'
    _description = 'vacation_settlement.vacation_settlement'

    is_settlement = fields.Boolean(string='Is Settlement', required=False)
    first_day_of_work = fields.Date(string='Last Effective Date', required=False)
    last_day_of_work = fields.Date(string='Last Day Of Work', required=False)
    days_of_work = fields.Integer(string='Total Work Days', required=False, compute='_compute_days_of_work', default=0)
    accrual_balance = fields.Float(string='Accrual Balance', required=False, compute='_compute_accrual_balance')
    effective_balance = fields.Float(string='Effective Balance', required=False, compute='_calculate_effective_balance', default=0)
    settlement_deductions_ids = fields.One2many(comodel_name='settlement.deduction', inverse_name='request_id', string='Settlement_deductions_ids', required=False)
    settlement_deserved_ids = fields.One2many(comodel_name='settlement.deserved', inverse_name='request_id', string='Settlement_deserved_ids', required=False)
    holiday_status_id = fields.Many2one("hr.leave.type", string="Time Off Type", required=True, readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    to_word = fields.Char(string='Amount In words', required=False, compute='_compute_to_word', default="")
    amount = fields.Float(compute='_compute_amount', string='Amount', required=False, default=0.0)
    with_visa = fields.Boolean(string='Vacation With Visa')
    payment_count = fields.Integer(string='Payment Count', compute='get_related_payments_count')

    related_payment_ids = fields.One2many(comodel_name='hr.payslip', inverse_name='settlement_id', string='Settlement Payments', required=False)
    unpaid_days = fields.Float('Unpaid Days',default=0)
    n_days = fields.Float('Number of Days',default=0)

    # @api.constrains('state', 'number_of_days', 'holiday_status_id')
    # def _check_holidays(self):
        
    #     mapped_days = self.mapped('holiday_status_id').get_employees_days(self.mapped('employee_id').ids)
    #     for holiday in self:
    #         if holiday.holiday_type != 'employee' or not holiday.employee_id or holiday.holiday_status_id.allocation_type == 'no':
    #             continue
    #         leave_days = mapped_days[holiday.employee_id.id][holiday.holiday_status_id.id]
    #         if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) == -1 or float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
    #             if not self.is_settlement:
    #                 raise ValidationError(_('The number of remaining time off is not sufficient for this time off type.\n'
    #                                     'Please also check the time off waiting for validation.'))
    #             else:
    #                 _logger.info("===========_check_holidays   =========== ")

    @api.constrains('related_payment_ids', 'payment_count')
    def _check_payments_number(self):
        if self.related_payment_ids:
            if self.payment_count > 0:
                raise ValidationError(
                        _("Number of payments should be one for every settlement"))

    @api.onchange('related_payment_ids')
    def onchange_related_payment_ids(self):
        if self.payment_count > 1:
            return self._check_payments_number()

    def open_related_payments(self):
        return {
            'name': _('Payments'),
            'domain': [('settlement_id', '=', self.id), ('is_settlement', '=', True)],
            'res_model': 'hr.payslip',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_related_payments_count(self):
        count = self.env['hr.payslip'].search_count([('settlement_id', '=', self.id)])
        self.payment_count = count

    def popup_message(self, title, body):
        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = body
        return {
            'name': title,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }

    def action_leave_settlement_payslip(self):
        view_id = self.env.ref('hr_payroll.view_hr_payslip_form')
        deserved_amount,ticketing_encashment,violations_penalties,deductions,loans,overtime,other_working_days,gosi = 0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
        for rec in self.settlement_deserved_ids:
            if rec.amount > 0:
                if rec.code == '2':
                    deserved_amount = rec.amount
                elif rec.code == '5':
                    ticketing_encashment = rec.amount
                elif rec.code == '4':
                    overtime = rec.amount
                elif rec.code == '7':
                    other_working_days = rec.amount
        for rec in self.settlement_deductions_ids:
            if rec.amount > 0:
                if rec.code == '2':
                    deductions += rec.amount
                elif rec.code == '3':
                    deductions += rec.amount
                elif rec.code == '4':
                    violations_penalties = rec.amount
                elif rec.code == '5':
                    loans = rec.amount
                elif rec.code == '6':
                    gosi = rec.amount
                elif rec.code == '7':
                    deductions += rec.amount
                elif rec.code == '8':
                    deductions += rec.amount

        input_line_ids = []
        get_ids = self.env['hr.payslip.input.type'].search(
            [('code', 'in', ['DVI1', 'DVI2', 'OA1', 'SOINS1', 'LON1', 'OTHERDAYS', 'DED1', 'LSETTLEMENT', 'TKTCASH'])])
        for item in get_ids:
            if item.code == 'LSETTLEMENT':
                line = (0, 0, {
                    'input_type_id': item.id,
                    'amount': deserved_amount
                })
            elif item.code == 'TKTCASH':
                line = (0, 0, {
                    'input_type_id': item.id,
                    'amount': ticketing_encashment
                })
            elif item.code == 'OA1':
                line = (0, 0, {
                    'input_type_id': item.id,
                    'amount': overtime
                })
            elif item.code == 'OTHERDAYS':
                line = (0, 0, {
                    'input_type_id': item.id,
                    'amount': other_working_days
                })
            elif item.code == 'LON1':
                line = (0, 0, {
                    'input_type_id': item.id,
                    'amount': loans
                })
            elif item.code == 'DED1':
                line = (0, 0, {
                    'input_type_id': item.id,
                    'amount': deductions
                })
            elif item.code == 'DVI1':
                line = (0, 0, {
                    'input_type_id': item.id,
                    'amount': violations_penalties
                })
            elif item.code == 'SOINS1':
                line = (0, 0, {
                    'input_type_id': item.id,
                    'amount': gosi
                })
            else:
                line = (0, 0, {
                    'input_type_id': item.id,
                    'amount': 0.0
                })
            input_line_ids.append(line)

        return {
            'name': _('New Leave Settlement Payslip'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'view_id': view_id.id,
            'views': [(view_id.id, 'form')],
            'context': {
                # 'default_settlement_id': self.id,
                'default_name': 'Leave Settlement'+'-' + self.employee_id.name,
                'default_employee_id': self.employee_id.id,
                'default_input_line_ids': input_line_ids,
                'default_is_settlement': True,
                'default_state': 'draft',

            }
        }

    @api.model
    def default_get(self, fields):
        res = super(VacationSettlement, self).default_get(fields)
        settlement_deductions_ids = []
        settlement_deserved_ids = []
        deductions_titles = {
            # '1': 'Current Account',
            '2': _('Remaining balance of iqama and Work permit'),
            '3': _('Deductions'),
            '4': _('Traffic Violations & Penalties'),
            '5': _('Loans'),
            '6': _('Social Insurance'),
            '7': _('Financial Consideration'),
            '8': _('Other - Visa Fees '),
        }
        deserved_titles = {
            # '1': 'Salary Payed with Same month',
            '2': _('Leave Settlement on the Period'),
            '3': _('End Of Service'),
            '4': _('Over Time '),
            '5': _('Ticketing Encashment'),
            '6': _('Holiday allowance'),
            '7': _('Working Days Salary'), #here
            # '8': 'Other',
        }
        index = 1
        for k, v in deductions_titles.items():
            line = (0, 0, {
                'request_id': self.id,
                'name': v,
                'code': k,
                'amount': 0.0
            })
            index = + 1
            settlement_deductions_ids.append(line)
        index = 1
        key = str(index)
        for k, v in deserved_titles.items():
            line = (0, 0, {
                'request_id': self.id,
                'name': v,
                'code': k,
                'amount': 0.0
            })
            settlement_deserved_ids.append(line)
        res.update({
            'settlement_deductions_ids': settlement_deductions_ids,
            'settlement_deserved_ids': settlement_deserved_ids
        })

        return res

    @api.constrains('first_day_of_work', 'last_day_of_work')
    def check_first_last_date(self):
        if self.last_day_of_work and self.first_day_of_work and self.first_day_of_work > self.last_day_of_work:
            raise ValidationError(
                _("Last date of work %s Can not be before first day date %s")
                % (self.last_day_of_work, self.first_day_of_work)
            )

    @api.depends('first_day_of_work', 'last_day_of_work')
    def _compute_days_of_work(self):
        if self.last_day_of_work and self.first_day_of_work:
            delta = self.last_day_of_work - self.first_day_of_work
            self.days_of_work = delta.days
        else:
            self.days_of_work = 0

    @api.depends('days_of_work', 'effective_balance','accrual_balance','employee_id')
    def _calculate_effective_balance(self):
        if not self.days_of_work == 0:
            if self.employee_id.annual_leave_days == '21':
                self.effective_balance = (self.days_of_work / 30) * 1.75
            elif self.employee_id.annual_leave_days == '30':
                self.effective_balance = (self.days_of_work / 30) * 2.5
            else:
                self.effective_balance = 0
        else:
            self.effective_balance = 0

    @api.depends('effective_balance')
    def _compute_to_word(self):
        self.to_word = ""
        total_deserved = 0.0
        total_deductions = 0.0
        if self.number_of_days >= 0:
            for bline in self.settlement_deserved_ids:
                total_deserved += bline.amount
            for dline in self.settlement_deductions_ids:
                total_deductions += dline.amount
            amount = round(total_deserved - total_deductions)
            self.amount = amount
            words = num2words(amount, lang='ar')
            words = words.replace('مئتين', 'مائتان')
            words = words.replace('ثلاثة مئة', 'ثلاثمائة')
            words = words.replace('أربعة مئة', 'أربعمائة')
            words = words.replace('خمسة مئة', 'خمسمائة')
            words = words.replace('خمسة مئة', 'خمسمائة')
            words = words.replace('ستة مئة', 'ستمائة')
            words = words.replace('سبعة مئة', 'سبعمائة')
            words = words.replace('ثمانية مئة', 'ثمانمائة')
            words = words.replace('تسعة مئة', 'تسعمائة')
            words = words.replace('،', ' و')
            self.to_word = words

    @api.depends('request_date_from', 'request_date_to')
    def _compute_amount(self):
        if self.is_settlement:
            # leave_salary = self.employee_id.contract_id.basic_salary + self.employee_id.contract_id.housing_allowance
            contract = self.env['hr.contract'].search([('employee_id','=',self.employee_id.id),('state','=','open')],limit=1)

            leave_salary = contract[0].wage
            if self.number_of_days != 0:
                self.settlement_deserved_ids[0].amount = ((self.number_of_days - self.unpaid_days)/30) * leave_salary
                self._compute_to_word()
            else:
                self._compute_to_word()
        else:
            self._compute_to_word()
        
    # @api.onchange('request_date_from','request_date_to')
    # def _compute_unpaid_days(self):
    #     self.unpaid_days = 0
    #     self.n_days = self.number_of_days
    #     if self.number_of_days > self.accrual_balance:
    #         self.unpaid_days= self.number_of_days - self.accrual_balance
    #         self.number_of_days = 0
    # @api.onchange('date_from', 'date_to', 'employee_id')
    # def _onchange_leave_dates(self):
    #     if self.date_from and self.date_to:
    #         self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id)['days']
    #         self.unpaid_days = 0
    #         self.n_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id)['days']
    #         if self.number_of_days > self.accrual_balance:
    #             self.unpaid_days= self.number_of_days - self.accrual_balance
    #             self.number_of_days =  self.accrual_balance
    #     else:
    #         self.number_of_days,self.n_days = 0 , 0
            

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.is_settlement:
            pass

    @api.onchange('is_settlement', 'holiday_status_id')
    def onchange_is_settlement(self):
        annual = self.env['hr.leave.type'].search([('code', '=', 'ANNUAL')]).id
        if self.is_settlement and self.state != 'validate':
            self.holiday_status_id = annual
            self.get_latest_effective_date()
        else:
            pass

    def get_latest_effective_date(self):
        c_date = self.env['hr.employee'].search([('id', '=', self.employee_id.id)]).last_effective_date
        self.first_day_of_work = c_date

    @api.depends('employee_id')
    def _compute_accrual_balance(self):
        annual = self.env['hr.leave.type'].search([('code', '=', 'ANNUAL')]).id
        allocations = self.env['hr.leave.allocation'].search([('holiday_status_id', '=', annual),
                                                       ('state', '=', 'validate'),
                                                       ('employee_id', '=', self.employee_id.id)])
        leave_requests = self.env['hr.leave'].search([('holiday_status_id', '=', annual),
                                                      ('state', '=', 'validate'),
                                                      ('employee_id', '=', self.employee_id.id)])
        allocated,requests = 0.0,0.0
        for rec in allocations:
            allocated += rec.number_of_days
        for req in leave_requests:
            requests += req.number_of_days
        self.accrual_balance = allocated - requests
    
    def calculate_input_line_ids(self):
        if not self.last_day_of_work:
            raise ValidationError("Please set Last day of work to calculate settlement!")
        for rec in self.settlement_deserved_ids:
            if rec.code == "7":
                rec.amount= self.get_worked_days_amount()
            if rec.code =="5":
                rec.amount = self.get_ticketing()

        for item in self.settlement_deductions_ids:
            if item.code == "6":
                item.amount = self.get_social_insurance()
            if item.code == "2":
                item.amount = self.get_remaining_balance_of_iqama()
            if item.code == "8":
                item.amount = self.get_vesa_fees()
    def get_worked_days_amount(self):
        if self.request_date_from.day != 1:
            days = self.last_day_of_work - datetime.strptime(self.last_day_of_work.strftime('%Y-%m-01'),'%Y-%m-%d' ).date()
            _logger.info("------- days "+str(days))
            return self.employee_id.contract_id.wage / 30 * (abs(days.days)+1)
    def get_ticketing(self):
        if self.employee_id.country_id:
            code = self.employee_id.country_id.code
            a = self.env['settlement.conf.ticket'].search([('country_id.code','=',code)])
            if self.employee_id.annual_leave_days == "30" and self.days_of_work > 360:
                return a.ticket
            if self.employee_id.annual_leave_days == "21" and self.days_of_work >720 :
                return a.ticket
            if self.employee_id.annual_leave_days == "21" and  self.days_of_work < 720 : 
                return a.ticket/2
        return 0
    def get_social_insurance(self):
        if self.employee_id.country_id.code == 'SA':
            return (self.employee_id.contract_id.basic_salary + self.employee_id.contract_id.housing_allowance)*0.1
        return 0 
    def get_remaining_balance_of_iqama(self):
        if self.employee_id.country_id.code != 'SA' and self.unpaid_days:
            return 800/30 * self.unpaid_days
    def get_vesa_fees(self):
        if self.employee_id.country_id.code != 'SA' and self.unpaid_days and self.with_visa:
            return 100/30 * self.unpaid_days
        return 0


class SettlementDeduction(models.Model):
    _name = 'settlement.deduction'
    _description = 'Settlement Deduction'

    name = fields.Char(string='Name',)
    code = fields.Char(string='Code', required=False)
    request_id = fields.Many2one(comodel_name='hr.leave', string='Request ID', required=False, ondelete='cascade')
    amount = fields.Float(string='Amount', required=False)
    description = fields.Char(string='Description', required=False)


class SettlementDeserved(models.Model):
    _name = 'settlement.deserved'
    _description = 'Settlement Deserved'

    name = fields.Char(string='Name',)
    code = fields.Char(string='Code', required=False)
    request_id = fields.Many2one(comodel_name='hr.leave', string='Request ID', required=False, ondelete='cascade')
    amount = fields.Float(string='Amount', required=False)
    description = fields.Char(string='Description', required=False)


class EffectiveDate(models.Model):
    _name = 'hr.effective.date'
    _inherit = ['mail.thread']
    _description = 'Effective Date'
    
    name = fields.Char(string='Name', required=True, readonly=True, default='New')
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),
                   ('confirmed', 'Confirmed')],
        required=True,default='draft')

    start_date = fields.Date(string='Start Date', required=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee Name', required=True)
    # emp_no = fields.Char(string="Employee No", required=False,
    #                             related='employee_id.emp_no', store=True,)
    identification_no = fields.Char(string="Identification ID", required=False,
                                    related='employee_id.identification_id', store=True, )
    job_title = fields.Many2one(string="Job Title", required=False,
                                related='employee_id.job_id', store=True,)
    dept_id = fields.Many2one(string="Department", required=False,
                              related='employee_id.department_id', store=True,)
    work_location = fields.Char(string="Work Location", required=False,
                                related='employee_id.work_location_id.name', store=True,)
    uploaded_file = fields.Binary(comodel_name='ir.attachment', string='Upload File', attachment=True, required=False)

    # @api.constrains('message_attachment_count')
    # def check_ir_attachment(self):
    #     for rec in self:
    #         if rec.message_attachment_count == 0:
    #             raise ValidationError("Please upload document for this record to confirmed!")

    def action_confirmed(self):
        # self.check_ir_attachment()
        self.state = 'confirmed'
        self.employee_id.state = 'active'
        # return self.popup_message('Confirmation', 'Employee state will be active after confirm!')

    def popup_message(self, title, body):
        view = self.env.ref('sh_message.sh_message_wizard')
        context = dict(self._context or {})
        context['message'] = body
        return {
            'name': title,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.effective.date') or _('New')
        result = super(EffectiveDate, self).create(vals)
        return result




class PayslipInput(models.Model):
    _inherit = 'hr.payslip'
    
    is_settlement = fields.Boolean(
        string='Is settlement', 
        required=False, default=False)
    settlement_id = fields.Many2one(comodel_name='hr.leave', string='Settlement Request No', required=False)

class SettllementConf(models.Model):
    _name = 'settlement.conf.ticket'
    _rec_name = 'country_id'
    _sql_constraints = [
                     ('country_id', 
                      'unique(country_id)',
                      'You connot have tow values for same country - it has to be unique!')]
    country_id = fields.Many2one('res.country')
    ticket = fields.Float('ticket value')

class HRDirectory(models.Model):
    _inherit = 'hr.employee'

    state = fields.Selection(string="Employee State", selection=[('active', 'Active'),
                                                                 ('onleave', 'On Leave'),
                                                                 ('suspended', 'Suspended'),
                                                                 ('resign', 'Resign'),
                                                                 ('terminated', 'Terminated')],
                             tracking=True, track_visibility='always', default='active', required=False, )
    emp_no = fields.Char(string="Employee Number", required=False,)
    joining_date = fields.Date(string='Joining Date')