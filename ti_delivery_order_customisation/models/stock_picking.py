# -*-coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    amsbio_order_line_ids = fields.Many2many(comodel_name="amsbio.order.line", relation="stock_sale_order_line_rel", compute="_compute_order_line_ids", store=True, string="AMSBIO Order Lines", help="These lines correspond to the sale order lines of the sale order for which this delivery is created. If the sale order was created from the inter company sale order functionality, then these lines correspond to the order lines of original sale order.")

    @api.depends("intercompany_sale_order", "origin")
    def _compute_order_line_ids(self):
        """
        In amsbio, we have "intercompany_sale_order" which stores the reference to sale order (of child companies) due to which this sale order was created.
        This method computes the order line details of the origin sale order.
        """
        for picking in self:
            order_reference = picking.intercompany_sale_order or picking.origin
            order = self.env["sale.order"].sudo().search([('name', '=', order_reference)], limit=1)
            if order:
                # Traverse through the order lines of the origin sale order and create amsbio.order.line records to store their detail
                lines = []
                for line in order.order_line:
                    vals = {
                        'price_unit': line.price_unit,
                        'product_description': line.name,
                        'quantity': line.product_uom_qty,
                        'price_subtotal': line.price_subtotal,
                        'order_reference': order.name,
                        'display_type': line.display_type
                    }
                    lines.append(vals)
                order_line_ids = self.env["amsbio.order.line"].create(lines)
                picking.amsbio_order_line_ids = [(6, 0, order_line_ids.ids)]
            else:
                picking.amsbio_order_line_ids = False
