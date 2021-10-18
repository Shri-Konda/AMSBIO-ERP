# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)




class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'


    def process(self):
        res = super(StockBackorderConfirmation,self).process()
        for picking in self.pick_ids:
            po_picking_ids = picking._get_po_picking_ids()
            if po_picking_ids:
                for po_picking in po_picking_ids.filtered(lambda po_pick: po_pick.state in ['assigned']):
                    backorder_confirmation_id = self.env['stock.backorder.confirmation'].with_context(button_validate_picking_ids=po_picking.ids).sudo().create({
                        'pick_ids': [(4, po_picking.id)],
                        'backorder_confirmation_line_ids': [(0, 0, {'to_backorder': True, 'picking_id': pick_id.id}) for pick_id in po_picking],
                    })
                    backorder_confirmation_id.process()
        return res

    def process_cancel_backorder(self):
        res = super(StockBackorderConfirmation,self).process_cancel_backorder()
        for picking in self.pick_ids:
            po_picking_ids = picking._get_po_picking_ids()
            if po_picking_ids:
                for po_picking in po_picking_ids.filtered(lambda po_pick: po_pick.state in ['assigned']):
                    backorder_confirmation_id = self.env['stock.backorder.confirmation'].with_context(button_validate_picking_ids=po_picking.ids).sudo().create({
                        'pick_ids': [(4, po_picking.id)],
                        'backorder_confirmation_line_ids': [(0, 0, {'to_backorder': False, 'picking_id': pick_id.id}) for pick_id in po_picking],
                    })
                    backorder_confirmation_id.process_cancel_backorder()

        return res



class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    def process(self):
        res = super(StockImmediateTransfer,self).process()
        for picking in self.pick_ids:
            po_picking_ids = picking._get_po_picking_ids()
            if po_picking_ids:
                for po_picking in po_picking_ids.filtered(lambda po_pick: po_pick.state in ['assigned']):
                    stock_immediate_transfer_id = self.env['stock.immediate.transfer'].with_context(button_validate_picking_ids=po_picking.ids).sudo().create({
                        'pick_ids': [(4, po_picking.id)],
                        'immediate_transfer_line_ids': [(0, 0, {'to_immediate': True, 'picking_id': pick_id.id}) for pick_id in po_picking],
                    })
                    stock_immediate_transfer_id.process()
        return res



class Picking(models.Model):
    _inherit = "stock.picking"


    
    def _get_po_picking_ids(self):
        if self.sale_id and self.sale_id.client_order_ref:
            po_picking = self.env['purchase.order'].sudo().search([('name','=',self.sale_id.client_order_ref)])
            if po_picking and po_picking.picking_ids:
                return po_picking.picking_ids


    def _set_qty_done(self,picking_movelines,po_picking_movelines):
        for pick_move in picking_movelines:
            ml = po_picking_movelines.filtered(lambda po_pick_moves: po_pick_moves.product_id.id==pick_move.product_id.id and po_pick_moves.product_uom_qty==pick_move.product_uom_qty)
            if ml:
                ml.qty_done = pick_move.qty_done


    def button_validate(self):
        for picking in self:
            po_picking_ids = picking._get_po_picking_ids()
            if po_picking_ids:
                picking_movelines = picking.move_lines.filtered(lambda m: m.state in ['assigned']).mapped('move_line_ids')
                for po_picking in po_picking_ids.filtered(lambda po_pick: po_pick.state in ['assigned']):
                    try:
                        po_picking_movelines = po_picking_ids.move_lines.filtered(lambda m: m.state in ['assigned']).mapped('move_line_ids')
                        po_picking._set_qty_done(picking_movelines,po_picking_movelines)
                    except Exception as e:
                        log_message = f'\n============ Something exceptional occur at button_validate ======\n Could not validate {po_picking.name}.\n{e}'
                        _logger.critical(log_message)

        res = super(Picking,self).button_validate()

        return res


    def _action_done(self):
        res = super(Picking,self)._action_done()

        for picking in self:
            move = None
            if picking.sale_id and not picking.purchase_id and picking.sale_id.auto_purchase_order_id:
                move = picking.sale_id._create_invoices(final=True)
            elif picking.sale_id and picking.purchase_id:
                move = picking.purchase_id.action_create_invoice()
                move = self.env['account.move'].sudo().browse([move.get('res_id',None)])
                if move:
                    move.write({
                        'ref'           : '%s-%s'%(move.ref,move.id),
                        'invoice_date'  : fields.Date.today(),
                    })
            move.action_post()
        return res


