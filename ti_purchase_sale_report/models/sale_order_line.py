# -*-coding: utf-8 -*-

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_supplier_id = fields.Many2one("res.partner", "Supplier", compute="_compute_product_supplier_id", store=True)
    original_customer = fields.Char("Original Customer", compute="_compute_original_customer", store=True)

    @api.depends("order_id.intercompany_sale_order", "order_partner_id")
    def _compute_original_customer(self):
        """"
            In amsbio, we do have intercompany setup where child companies create purchase order to main company and sale order is created for that purchase order.
        """
        for order_line in self:
            intercompany_sale_order = order_line.order_id.intercompany_sale_order
            if intercompany_sale_order:
                order_id = self.env["sale.order"].sudo().search([('name', '=', intercompany_sale_order)], limit=1)
                order_line.original_customer = order_id.partner_id.name
            else:
                order_line.original_customer = order_line.order_id.partner_id.name
                
    @api.depends("product_id.seller_ids")
    def _compute_product_supplier_id(self):
        for order_line in self:
            seller = self.env["product.supplierinfo"].search([('company_id', '=', order_line.company_id.id), ('product_tmpl_id', '=', order_line.product_template_id.id)], limit=1)
            if seller:
                order_line.product_supplier_id = seller.display_name
            else:
                order_line.product_supplier_id = False