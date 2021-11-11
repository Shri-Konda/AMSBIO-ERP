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


class StockMove(models.Model):
    _inherit = "stock.move"

    next_serial = fields.Char('First SN',readonly=True)

    def ti_action_assign_serial_show_details(self):
        """ On `self.move_line_ids`, assign `lot_name` according to
        `self.next_serial` before returning `self.action_show_details`.
        """
        for rec in self:
            rec.ensure_one()
            if not rec.next_serial:
                rec.next_serial = rec.company_id.product_tracking_number
                rec.action_clear_lines_show_details()
                rec._generate_serial_numbers()
        return True


    def _generate_serial_numbers(self, next_serial_count=False):
        """ This method will generate `lot_name` from a string (field
        `next_serial`) and create a move line for each generated `lot_name`.
        """
        self.ensure_one()

        if not next_serial_count:
            next_serial_count = self.next_serial_count
        # We look if the serial number contains at least one digit.
        caught_initial_number = regex_findall("\d+", self.next_serial)
        if not caught_initial_number:
            raise UserError(_('The serial number must contain at least one digit.'))
        # We base the serie on the last number find in the base serial number.
        initial_number = caught_initial_number[-1]
        padding = len(initial_number)
        # We split the serial number to get the prefix and suffix.
        splitted = regex_split(initial_number, self.next_serial)
        # initial_number could appear several times in the SN, e.g. BAV023B00001S00001
        prefix = initial_number.join(splitted[:-1])
        suffix = splitted[-1]
        initial_number = int(initial_number)

        lot_names = []
        for i in range(0, next_serial_count):
            lot_names.append('%s%s%s' % (
                prefix,
                str(initial_number + i).zfill(padding),
                suffix
            ))

        move_lines_commands = self._generate_serial_move_line_commands(lot_names)
        self.write({'move_line_ids': move_lines_commands})
        self.company_id.product_tracking_number = '%s%s%s' % (prefix,str(int(self.company_id.product_tracking_number)+1 + i).zfill(padding),suffix)
        return True