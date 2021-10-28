# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockImmediateTransfer(models.TransientModel):
    _inherit = "stock.immediate.transfer"

    is_receipt = fields.Boolean("Is Receipt", compute="_compute_is_receipt", help="If the current picking is of receipt type.")

    @api.depends("pick_ids")
    def _compute_is_receipt(self):
        for transfer in self:
            transfer.is_receipt = "incoming" in transfer.pick_ids.mapped("picking_type_code")
            