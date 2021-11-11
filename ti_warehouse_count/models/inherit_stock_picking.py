# -*- coding: utf-8 -*-

# https://support.targetintegration.com/issues/5907
# https://support.targetintegration.com/issues/5908


from odoo import api, fields, models, tools,SUPERUSER_ID
from odoo.tools.float_utils import float_compare
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
                for po_picking in po_picking_ids.filtered(lambda po_pick: po_pick.state in ['assigned','confirmed']):
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
                for po_picking in po_picking_ids.filtered(lambda po_pick: po_pick.state in ['assigned','confirmed']):
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
                for po_picking in po_picking_ids.filtered(lambda po_pick: po_pick.state in ['assigned','confirmed']):
                    pickings_to_backorder = po_picking._check_backorder()
                    pickings_to_immediate = po_picking._check_immediate()
                    if pickings_to_immediate and not pickings_to_backorder:
                        stock_immediate_transfer_id = self.env['stock.immediate.transfer'].with_context(button_validate_picking_ids=po_picking.ids).sudo().create({
                            'pick_ids': [(4, po_picking.id)],
                            'immediate_transfer_line_ids': [(0, 0, {'to_immediate': True, 'picking_id': pick_id.id}) for pick_id in po_picking],
                        })
                        stock_immediate_transfer_id.process()
                    elif not pickings_to_immediate and not pickings_to_backorder:
                        po_picking.button_validate()
        return res



class Picking(models.Model):
    _inherit = "stock.picking"


    client_order_ref = fields.Char(string='Customer Reference', copy=False)

    
    def _get_po_picking_ids(self):
        self = self.with_user(SUPERUSER_ID)
        if self.sale_id and self.sale_id.auto_purchase_order_id:
            po_picking = self.sale_id.auto_purchase_order_id
            if po_picking and po_picking.picking_ids:
                return po_picking.picking_ids


    def _set_qty_done(self,picking_movelines,po_picking_movelines):
        for pick_move,po_pick_move in zip(picking_movelines,po_picking_movelines):
            if pick_move.product_id.tracking == 'none' and po_pick_move.product_id.tracking == 'none':
                if po_pick_move.product_id.id==pick_move.product_id.id and po_pick_move.product_uom_qty==pick_move.product_uom_qty:
                    po_pick_move.qty_done = pick_move.qty_done


    def _set_extra_moves(self,picking_movelines,po_picking_movelines):
        for pick_moveline , po_pick_moveline in zip(picking_movelines, po_picking_movelines):
            for po_moveline in po_pick_moveline.mapped('move_line_ids')[len(pick_moveline.mapped('move_line_ids')):]:
                po_moveline.qty_done = 0



    def button_validate(self):
        for picking in self:
            po_picking_ids = picking._get_po_picking_ids()
            if po_picking_ids:
                picking_movelines = picking.move_lines.filtered(lambda m: m.state in ['assigned','partially_available'])
                for po_picking in po_picking_ids.filtered(lambda po_pick: po_pick.state in ['assigned']):
                    try:
                        po_picking_movelines = po_picking_ids.move_lines.filtered(lambda m: m.state in ['assigned'])
                        for po_picking_move_line in po_picking_movelines:
                            if po_picking_move_line.product_id.tracking != 'none':
                                po_picking_move_line.next_serial = None
                                po_picking_move_line.ti_action_assign_serial_show_details()
                                po_picking._set_extra_moves(picking_movelines,po_picking_movelines)
                            elif po_picking_move_line.product_id.tracking == 'none':
                                po_picking._set_qty_done(picking_movelines.mapped('move_line_ids'),po_picking_movelines.mapped('move_line_ids'))
                    except Exception as e:
                        log_message = f'\n============ Something exceptional occur at button_validate ======\n Could not validate {po_picking.name}.\n{e}'
                        _logger.critical(log_message)

        res = super(Picking,self).button_validate()
        return res


    def _action_done(self):
        res = super(Picking,self)._action_done()
        self = self.with_user(SUPERUSER_ID)
        for picking in self:
            move = None
            if picking.sale_id and not picking.purchase_id and picking.sale_id.auto_purchase_order_id:
                move = picking.sale_id._create_invoices(final=True)
                move.action_post()
            elif picking.sale_id and picking.purchase_id:
                move = picking.purchase_id.action_create_invoice()
                move = self.env['account.move'].sudo().browse([move.get('res_id',None)])
                if move:
                    move.write({
                        'ref'           : '%s-%s'%(move.ref,move.id),
                        'invoice_date'  : fields.Date.today(),
                    })
                move.action_post()

                original_so = picking.purchase_id._get_sale_orders()
                original_mv = original_so._create_invoices(final=True)
                original_mv.action_post()
        return res


