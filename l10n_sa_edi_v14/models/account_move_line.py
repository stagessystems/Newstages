from odoo import models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_downpayment_lines(self):
        return self.sale_line_ids.filtered('is_downpayment').invoice_lines.filtered(lambda line: line.move_id._is_downpayment())
