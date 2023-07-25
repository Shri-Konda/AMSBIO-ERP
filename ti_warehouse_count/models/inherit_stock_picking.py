# -*- coding: utf-8 -*-

# https://support.targetintegration.com/issues/5907
# https://support.targetintegration.com/issues/5908

import logging
from odoo.tools.translate import _
from odoo.tools.float_utils import float_compare
from odoo import api, fields, models, tools,SUPERUSER_ID


_logger = logging.getLogger(__name__)


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'


    def process(self):
        "When backorder is created for a transfer, we have to create backorder for the origin picking as well."

        res = super(StockBackorderConfirmation,self).process()
        for picking in self.pick_ids:
            origin_pickings = picking._get_source_po_pickings()
            if origin_pickings:
                for origin_picking in origin_pickings.filtered(lambda picking: picking.state in ["confirmed", "assigned"]):
                    backorder_confirmation_id = self.env['stock.backorder.confirmation'].with_context(button_validate_picking_ids=origin_picking.ids).sudo().create({
                        'pick_ids': [(4, origin_picking.id)],
                        'backorder_confirmation_line_ids': [(0, 0, {'to_backorder': True, 'picking_id': pick_id.id}) for pick_id in origin_picking],
                    })
                    backorder_confirmation_id.process()
        return res

    def process_cancel_backorder(self):
        "When backorder is cancelled for a transfer, we have to carry forward the same backorder cancellation for the origin picking as well."

        res = super(StockBackorderConfirmation,self).process_cancel_backorder()
        for picking in self.pick_ids:
            origin_pickings = picking._get_source_po_pickings()
            if origin_pickings:
                for origin_picking in origin_pickings.filtered(lambda po_pick: po_pick.state in ['assigned','confirmed']):
                    backorder_confirmation_id = self.env['stock.backorder.confirmation'].with_context(button_validate_picking_ids=origin_picking.ids).sudo().create({
                        'pick_ids': [(4, origin_picking.id)],
                        'backorder_confirmation_line_ids': [(0, 0, {'to_backorder': False, 'picking_id': pick_id.id}) for pick_id in origin_picking],
                    })
                    backorder_confirmation_id.process_cancel_backorder()

        return res



class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    def process(self):
        res = super(StockImmediateTransfer,self).process()
        for picking in self.pick_ids:
            origin_pickings = picking._get_source_po_pickings()
            if origin_pickings:
                for origin_picking in origin_pickings.filtered(lambda picking: picking.state in ["confirmed", "assigned"]):
                    is_immediate = origin_picking._check_immediate()
                    # since main transfer was immediately transferred, we will do the immediate transfer on it's origin transfer as well
                    if is_immediate:
                        stock_immediate_transfer_id = self.env["stock.immediate.transfer"].with_context(button_validate_picking_ids=origin_picking.ids).sudo().create({
                            'pick_ids': [(4, origin_picking.id)],
                            'immediate_transfer_line_ids': [(0, 0, {'to_immediate': True, 'picking_id': pick.id}) for pick in origin_picking]
                        })
                        stock_immediate_transfer_id.process()
        return res



class Picking(models.Model):
    _inherit = "stock.picking"


    client_order_ref = fields.Char(string='Customer Reference', copy=False)
    intercompany_sale_order = fields.Char('Intercompany Sales Order')

    
    def _get_source_po_pickings(self):
        "Returns the receipts of the source purchase order"

        self = self.with_user(SUPERUSER_ID)
        if self.sale_id and self.sale_id.auto_purchase_order_id:
            return self.sale_id.auto_purchase_order_id.picking_ids
        else:
            return self.browse()
    
    def _set_done_qty_on_source_moves(self, picking_moves, source_picking_moves):
        """Set the done qty of the source product moves based on qty done for move."""

        for source_move in source_picking_moves:
            done_qty = picking_moves.filtered(lambda move: move.product_id.id == source_move.product_id.id).qty_done or 0.0
            if done_qty:
                source_move.qty_done = done_qty


    def _set_extra_moves(self,picking_movelines,po_picking_movelines):
        for pick_moveline in picking_movelines:
            for po_pick_moveline in po_picking_movelines:
                for po_moveline in po_pick_moveline.mapped('move_line_ids')[len(pick_moveline.mapped('move_line_ids')):]:
                    po_moveline.qty_done = 0

    def _set_done_qty_on_source_picking(self, source_picking):
        "Set done qty on the source picking"

        picking_moves = self.move_lines.filtered(lambda move: move.state in ["assigned", "partially_available"])
        origin_moves = source_picking.move_lines.filtered(lambda move: move.state in ["assigned"])
        for origin_move in origin_moves:
            if origin_move.product_id.tracking != 'none':
                origin_move.next_serial = None
                origin_move.ti_action_assign_serial_show_details()
                source_picking._set_extra_moves(picking_moves, origin_moves)
            elif origin_move.product_id.tracking == 'none':
                # Set done qty of the source moves based on the current product moves 
                source_picking._set_done_qty_on_source_moves(picking_moves.mapped('move_line_ids'), origin_moves.mapped('move_line_ids'))

    def button_validate(self):
        """
        When we validate a transfer, we have to also validate the pickings from the source purchase order.
        """
        for picking in self:
            source_pickings = picking._get_source_po_pickings()
            if source_pickings:
                for source_picking in source_pickings.filtered(lambda po_pick: po_pick.state in ['assigned']):
                    try:
                        picking._set_done_qty_on_source_picking(source_picking)
                        source_picking.button_validate()
                    except Exception as e:
                        _logger.critical(f"\n==>Error while calling button_validate on {source_picking.name}: {e}\n")
        result = super(Picking, self).button_validate()
        return result
