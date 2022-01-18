# -*-coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.float_utils import float_compare

class StockPicking(models.Model):
    _inherit = "stock.picking"


    searched_reserve_status = fields.Selection([
        ('full', "Fully Ready"),
        ('partial', "Partially Ready"),
        ('complete', "Complete"),
        ('cancel', "Cancelled"),
    ],string="Reserved Status",help="*Fully Ready: If all the products in the delivery order are reserved.\n*Partially Ready: If some of the products in the delivery order are reserved.")

    reserve_status = fields.Selection([
        ('full', "Fully Ready"),
        ('partial', "Partially Ready"),
        ('complete', "Complete"),
        ('cancel', "Cancelled"),
    ],compute="_compute_reserver_status", string="Reserved Status",help="*Fully Ready: If all the products in the delivery order are reserved.\n*Partially Ready: If some of the products in the delivery order are reserved.")

    @api.depends("move_lines")
    def _compute_reserver_status(self):
        for picking in self:
            status = None
            if picking.state=='done':
                status = "complete"
            elif picking.state=='cancel':
                status = "cancel"
            else:
                for move in picking.move_lines:
                    if move.product_id.type == 'product':
                        rounding = move.product_id.uom_id.rounding
                        if float_compare(move.product_uom_qty, move.reserved_availability, precision_rounding=rounding) == 0:
                            status = "full"
                        else:
                            status = "partial"
                            break
            picking.reserve_status = status
            picking.searched_reserve_status = status

