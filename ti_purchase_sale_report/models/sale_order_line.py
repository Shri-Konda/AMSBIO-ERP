# -*-coding: utf-8 -*-

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_supplier = fields.Char("Supplier", compute="_compute_product_supplier", store=True)
    original_customer = fields.Char("Original Customer", compute="_compute_original_customer", store=True)
    order_partner_shipping_city = fields.Char(related="order_id.partner_shipping_id.city", store=True, string="Delivery City")
    order_partner_shipping_zip = fields.Char(related="order_id.partner_shipping_id.zip", store=True, string="Delivery Postal Code")

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
    def _compute_product_supplier(self):
        for order_line in self:
            seller = self.env["product.supplierinfo"]
            # if the product is eu supplier product, then avoid checking for company pricelits
            if order_line.product_id.is_eu_supplier:
                companies_contacts = self.env["res.company"].sudo().search([]).mapped("partner_id")
                seller = self.env["product.supplierinfo"].sudo().search([('partner_id', 'not in', companies_contacts.ids), ('product_tmpl_id', '=', order_line.product_template_id.id)], limit=1)
            # if product still does not have supplier, then include all the pricelits
            if not seller:
                seller = self.env["product.supplierinfo"].sudo().search([('product_tmpl_id', '=', order_line.product_template_id.id)], limit=1)
            if seller:
                order_line.product_supplier = seller.display_name
            else:
                order_line.product_supplier = False

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    amount_currency = fields.Monetary(group_operator="sum")
