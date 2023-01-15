# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
import datetime
import calendar
_logger = logging.getLogger(__name__)

def last_day_of_month(any_day):
    # get close to the end of the month for any day, and add 4 days 'over'
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    # subtract the number of remaining 'overage' days to get last day of current month, or said programattically said, the previous day of the first of next month
    return next_month - datetime.timedelta(days=next_month.day)

class hr_extend(models.Model):
    _inherit = 'hr.employee'

    attach_ids = fields.One2many('hr.emp.doc','employee_id')
    def leave_request(self):
        return {
            'name': _('Leave request'),
            # 'domain': [('employee_id', '=', self.id)],
            'res_model': 'hr.leave',
            'view_id': False,
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context':  {'default_employee_id': self.id}
        }
class EmpDocs(models.Model):
    _name = 'hr.emp.doc'

    name = fields.Char('Name')
    attach = fields.Binary('File')
    employee_id = fields.Many2one('hr.employee')

class LeaveAcrualPlan(models.Model):
    _inherit = 'hr.leave.accrual.plan'
    code = fields.Char()
    
class HRContractINH(models.Model):
    _inherit = 'hr.contract'
    allocation_id = fields.Many2one('hr.leave.allocation')
    salary = fields.Float(compute='_compute_salary')

    def _compute_salary(self):
        for rec in self:
            salary = rec.wage + rec.hra + rec.travel_allowance + rec.other_allowance + rec.medical_allowance + rec.da + rec.meal_allowance
            rec.salary = salary
    def create_allocate(self):
        leave = self.env['hr.leave']
        accrual = self.env['hr.leave.accrual.plan']
        allocation = self.env['hr.leave.allocation']
        holiday_status = self.env['hr.leave.type']
        name = self.employee_id.name 
        holiday_status_id = holiday_status.search([('id','=',1)],limit=1)
        if self.employee_id.annual_leave_days == '21':
            accrual_id = accrual.search([('code','=','JN')],limit=1)
        if self.employee_id.annual_leave_days == '30':
            accrual_id = accrual.search([('code','=','SN')],limit=1)

        vals = {'name':name,
                        'holiday_status_id':holiday_status_id[0].id,
                        'allocation_type': 'accrual',
                        'accrual_plan_id' : accrual_id[0].id,
                        'holiday_type' : 'employee',
                        'date_from' : self.date_start,
                        'employee_id' : self.employee_id.id
                        # 'company_id':self.employee_id.company_id.id
                        }
        _logger.info("============"+str(vals))
        if not self.allocation_id:
            res = allocation.sudo().create(vals) 
            self.allocation_id = res.id
        urg_holiday_status_id = holiday_status.search([('code','=','URG')],limit=1)
        vals['allocation_type'] = 'regular'
        vals['holiday_status_id'] = urg_holiday_status_id[0].id
        vals.pop('accrual_plan_id')
        vals['number_of_days'] = 60
        old = allocation.search([('employee_id','=',self.employee_id.id),('holiday_status_id.code','=','URG')])
        _logger.info("----------------"+str(old))
        _logger.info("----------------"+str(len(old)))
        if len(old) == 0:
            urg = allocation.sudo().create(vals) 
        # return res
class HrPayslipRunInh(models.Model):
    _inherit = 'hr.payslip.run'
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve1', 'first approve'),
        ('approve2', 'account verify'),
        ('approve3', 'DM approve'),
        ('done', 'Done'),
        ('close', 'Close'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')

    def approve1(self):
        self.state = 'approve1'
    def approve2(self):
        self.state = 'approve2'
    def approve3(self):
        self.state = 'approve3'
class HrPayslipInh(models.Model):
    _inherit = 'hr.payslip'
    over_time = fields.Float('Over Time',default=0)
# class companyinh(models.Model):
#     _inherit = 'res.company'
#     slip_date=fields.Date()
class HrPayslipRunInh(models.Model):
    _inherit = 'hr.payslip.run'
    
    def auto_payslips(self):
        batch_date = self.env['ir.config_parameter'].get_param('hr_extend.batch_date')
        _logger.info("******************"+str(datetime.datetime.today().day)+str(batch_date))
        if str(datetime.datetime.today().day) == str(batch_date) :
            company_ids = self.env['res.company'].search([])
            from_date = datetime.datetime.today().replace(day=1).date()
            _logger.info("======================="+str(from_date))
            payslips = self.env['hr.payslip']
            to_date = last_day_of_month(datetime.datetime.today().date())
            _logger.info("======================="+str(to_date))
            for company in company_ids:
                emp_ids = self.env['hr.employee'].search([('company_id','=',company.id)])
                if emp_ids:
                    payslip_run_id = self.create({"name":str(company.name)})
                    for employee in emp_ids:
                        if employee.state == 'active':
                            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
                            _logger.info("================="+str(slip_data))
                            res = {
                                'employee_id': employee.id,
                                'name': slip_data['value'].get('name'),
                                'struct_id': slip_data['value'].get('struct_id'),
                                'contract_id': slip_data['value'].get('contract_id'),
                                'payslip_run_id': payslip_run_id.id,
                                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                                'date_from': from_date,
                                'date_to': to_date,
                                'credit_note': False,
                                'company_id': employee.company_id.id,
                            }
                            _logger.info("-----------------"+str(res))
                            payslips += self.env['hr.payslip'].create(res)
                            payslips.compute_sheet()


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    batch_date = fields.Integer(string='Batch Date',config_parameter='hr_extend.batch_date')

