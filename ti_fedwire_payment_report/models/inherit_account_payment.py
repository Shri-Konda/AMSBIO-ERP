# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# https://support.targetintegration.com/issues/6344

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from logging import getLogger
_logger = getLogger(__name__)

class Account_Payment(models.Model):
    _inherit = 'account.payment'

    def action_generate_fedwire_payment(self):
        payment_date = set(self.mapped('date'))
        if len(payment_date) >= 2:
            raise UserError(_('Please Select Payments with same date.'))
        else:
            return self.env.ref('ti_fedwire_payment_report.ti_amsbio_payment_fedwire_transaction_report').report_action(self)