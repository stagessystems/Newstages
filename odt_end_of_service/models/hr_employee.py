# -*- coding: utf-8 -*-
# 
#    OpenERP, Open Source Management Solution

#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # @api.multi
    def _compute_eos_leaves(self):
        self._cr.execute("""SELECT
                sum(h.number_of_days) as days,
                h.employee_id
            from
                hr_leave h
                join hr_holidays_status s on (s.id=h.holiday_status_id)
            where
                h.state='validate' and
                h.type = 'remove' and
                s.is_depend_eos=True and
                h.employee_id in %s
            group by h.employee_id""", (tuple(self.ids),))

        res = self._cr.dictfetchall()
        for re in res:
            self.browse(re['employee_id']).total_eos_leaves = -re['days']

    total_eos_leaves = fields.Float('No of Leaves Depend EOS', compute='_compute_eos_leaves')