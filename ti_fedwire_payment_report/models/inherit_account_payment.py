# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# https://support.targetintegration.com/issues/6344

from odoo import models, _
from odoo.exceptions import UserError
from logging import getLogger
_logger = getLogger(__name__)

class Account_Payment(models.Model):
    _inherit = 'account.payment'

    def action_generate_fedwire_payment(self):
        #Fedwire code is important to print USD report, if any record doesn't have fedwire code, we need to raise an error
        for record in self:
            if record.partner_id.supplier_rank and not record.partner_id.fedwire_code:
                raise UserError(_(f"Please make sure vendor has Fedwire Code. Missing code for {record.partner_id.name}"))

            if record.partner_id.supplier_rank and not record.partner_bank_id:
                raise UserError(_(f"Missing Recipient Bank Account for payment {record.name}"))

        payment_date = set(self.mapped('date'))
        if len(payment_date) >= 2:
            raise UserError(_('Please Select Payments with same date.'))
        else:
            report = self.env["ir.actions.report"]._get_report_from_name("ti_fedwire_payment_report.report_template_fedwire_payment")
            return report.report_action(self)