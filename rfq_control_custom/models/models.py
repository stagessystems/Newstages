from odoo import models, fields, api , _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import datetime
import datetime
from datetime import datetime


class RfqControlCustom(models.Model):
    _inherit = "crossovered.budget.lines"


    department_id = fields.Many2one("hr.department",string="department")

class ApprovalReq(models.Model):
    _inherit = 'approval.request'

    def action_confirm(self):
        d_date = datetime.today()
        for rec in self:
            if rec.product_line_ids:
                for line in rec.product_line_ids:
                    if not line.product_id.property_account_expense_id:
                        raise ValidationError(
                            _("No expense account available for One Product in list!")
                        )
                    else:
                        position_ids = self.env["account.budget.post"].search(
                            [
                                ("account_ids", "in", line.product_id.property_account_expense_id.id),
                                ("company_id", "=", self.env.user.company_id.id),
                            ]

                        )
                        for post in position_ids:
                            budget_lines = self.env["crossovered.budget.lines"].search(
                                [
                                    ("general_budget_id", "=", post.id),
                                    ("department_id", "=", self.env.user.department_id.id),
                                ],limit=1

                            )
                            print(budget_lines.crossovered_budget_id.state)
                            if budget_lines:
                                if budget_lines.crossovered_budget_id.state == 'done' and d_date.date() >= budget_lines.crossovered_budget_id.date_from and d_date.date() <= budget_lines.crossovered_budget_id.date_to  :
                                    if not line.product_id.standard_price or line.product_id.standard_price == 0 :
                                        raise ValidationError(
                                            _("No product cost for one item in list !:" + line.product_id.name )
                                        )
                                    elif (line.product_id.standard_price * line.quantity) + abs(budget_lines.theoritical_amount) > abs(budget_lines.planned_amount):
                                            raise ValidationError(
                                                _("The planned budget will be exceeded !:")
                                            )

                            else:
                                raise ValidationError(
                                    _("No budget available !")
                                )


        super(ApprovalReq, self).action_confirm()
        pass
