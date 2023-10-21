# -*-coding: utf-8 -*-

import logging
from odoo import models, fields, api
from odoo.tools.float_utils import float_compare, float_is_zero

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"


    searched_reserve_status = fields.Selection([
        ('nothing', "Nothing Ready"),
        ('full', "Fully Ready"),
        ('partial', "Partially Ready"),
        ('complete', "Complete"),
        ('cancel', "Cancelled"),
    ],string="Reserved Status", help="*Fully Ready: If all the products in the delivery order are reserved.\n*Partially Ready: If some of the products in the delivery order are reserved.")

    reserve_status = fields.Selection([
        ('nothing', "Nothing Ready"),
        ('full', "Fully Ready"),
        ('partial', "Partially Ready"),
        ('complete', "Complete"),
        ('cancel', "Cancelled"),
    ],compute="_compute_reserve_status", string="Reserved Status", help="*Fully Ready: If all the products in the delivery order are reserved.\n*Partially Ready: If some of the products in the delivery order are reserved.")

    @api.depends("move_ids.reserved_availability", "state")
    def _compute_reserve_status(self):
        for picking in self:
            if picking.state == 'done':
                status = "complete"
            elif picking.state == 'cancel':
                status = "cancel"
            elif picking.state == "draft":
                status = "nothing"
            else:
                product_moves = picking.move_ids.filtered(lambda move: move.product_id.detailed_type == "product")
                reserved_moves = product_moves.filtered(lambda move: not float_is_zero(move.reserved_availability, precision_rounding=move.product_uom.rounding))
                if reserved_moves:
                    fully_reserved_moves = reserved_moves.filtered(lambda move: float_compare(move.product_uom_qty, move.reserved_availability, precision_rounding=move.product_uom.rounding) == 0)
                    if len(fully_reserved_moves) == len(product_moves):
                        status = "full"
                    else:
                        status = "partial"
                else:
                    status = "nothing"
            picking.reserve_status = status
            picking.searched_reserve_status = status

