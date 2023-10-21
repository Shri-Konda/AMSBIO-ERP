# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# https://support.targetintegration.com/issues/6344

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from re import findall as regex_findall
from re import split as regex_split
from logging import getLogger
_logger = getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    product_tracking_number = fields.Char('Product Tracking Number',default='1')
    route_id = fields.Many2one('stock.route', string='Route', domain=[('sale_selectable', '=', True)], ondelete='restrict', check_company=True)


class StockMove(models.Model):
    _inherit = "stock.move"

    next_serial = fields.Char('First SN',readonly=True)

    def ti_action_assign_serial_show_details(self):
        """ On `self.move_line_ids`, assign `lot_name` according to
        `self.next_serial` before returning `self.action_show_details`.
        """
        for rec in self:
            rec.ensure_one()
            rec.next_serial = rec.company_id.product_tracking_number
            rec.action_clear_lines_show_details()
            rec._generate_serial_numbers()
        return True
    
class StockLot(models.Model):
    _inherit = "stock.lot"
    
    @api.model
    def generate_lot_names(self, first_lot, count):
        "override method to update product tracking number on company"

        # We look if the first lot contains at least one digit.
        caught_initial_number = regex_findall(r"\d+", first_lot)
        if not caught_initial_number:
            return self.generate_lot_names(first_lot + "0", count)
        # We base the series on the last number found in the base lot.
        initial_number = caught_initial_number[-1]
        padding = len(initial_number)
        # We split the lot name to get the prefix and suffix.
        splitted = regex_split(initial_number, first_lot)
        # initial_number could appear several times, e.g. BAV023B00001S00001
        prefix = initial_number.join(splitted[:-1])
        suffix = splitted[-1]
        initial_number = int(initial_number)

        lot_names = []
        for i in range(0, count):
            lot_names.append('%s%s%s' % (
                prefix,
                str(initial_number + i).zfill(padding),
                suffix
            ))

        # set the tracking number in company level as well
        self.company_id.product_tracking_number = '%s%s%s' % (prefix,str(int(self.company_id.product_tracking_number)+1 + i).zfill(padding),suffix)
        return lot_names


class ResPartner(models.Model):
    _inherit = "res.partner"

    type = fields.Selection(selection_add=[('private', "Broker")])


class Account_Payment(models.Model):
    _inherit = 'account.payment'

    def action_generate_bacs_payment(self):
        payment_date = set(self.mapped('date'))
        if len(payment_date) >= 2:
            raise UserError(_('Please Select Payments with same date.'))
        else:
            report = self.env["ir.actions.report"]._get_report_from_name("ti_warehouse_count.report_template_bacs_payment")
            return report.report_action(self)