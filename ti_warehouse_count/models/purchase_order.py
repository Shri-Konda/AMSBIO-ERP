# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# https://support.targetintegration.com/issues/6728

from logging import getLogger
from datetime import datetime
from odoo.osv import expression
from psycopg2 import IntegrityError
from odoo import api, fields, models, _


_logger = getLogger(__name__)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    uk_warehouse_qty = fields.Float('Available Qty For UK Warehouse', readonly=True, compute='_compute_warehouse_qty')
    uk_us_warehouse_qty = fields.Float('Available Qty For UK-US Warehouse', readonly=True, compute='_compute_warehouse_qty')
    ch_warehouse_qty = fields.Float('Available Qty For CH Warehouse', readonly=True, compute='_compute_warehouse_qty')
    bv_warehouse_qty = fields.Float('Available Qty For BV Warehouse', readonly=True, compute='_compute_warehouse_qty')

    converted_price_unit = fields.Float(compute='_compute_converted_price_subtotal', string='Unit Price in USD',)
    converted_price_subtotal = fields.Float(compute='_compute_converted_price_subtotal', string='Subtotal in USD',)


    @api.depends('product_qty', 'price_unit', 'taxes_id', 'price_subtotal', 'price_unit')
    def _compute_converted_price_subtotal(self):
        IrDefault = self.env['ir.default'].sudo()
        currency_id = IrDefault.get('res.config.settings', 'exported_currency')
        currency_id = self.env['res.currency'].sudo().browse([currency_id])
        for line in self:
            line.converted_price_subtotal = line.order_id.currency_id._convert(line.price_subtotal, currency_id, line.company_id, fields.Date.context_today(line))
            line.converted_price_unit = line.order_id.currency_id._convert(line.price_unit, currency_id, line.company_id, fields.Date.context_today(line))


    @api.depends('product_id')
    def _compute_warehouse_qty(self):
        for line in self:
            line.uk_warehouse_qty = 0
            line.uk_us_warehouse_qty = 0
            line.ch_warehouse_qty = 0
            line.bv_warehouse_qty = 0
            IrDefault = self.env['ir.default'].sudo()
            company_id = IrDefault.get('res.config.settings', 'warehouse_count')
            company_id = self.env['res.company'].sudo().browse([company_id])
            if company_id and line.company_id.id == company_id.id:
                uk_warehouse = self.env["stock.warehouse"].sudo().search([("code", '=', "UK")], limit=1)
                us_warehouse = self.env["stock.warehouse"].sudo().search([("code", '=', "US")], limit=1)
                ch_warehouse = self.env["stock.warehouse"].sudo().search([("code", '=', "CH")], limit=1)
                bv_warehouse = self.env["stock.warehouse"].sudo().search([("code", '=', "NL")], limit=1)

                if uk_warehouse:
                    line.uk_warehouse_qty = line.product_id.with_context(warehouse=uk_warehouse.id).free_qty

                if us_warehouse:
                    line.uk_us_warehouse_qty = line.product_id.with_context(warehouse=us_warehouse.id).free_qty

                if ch_warehouse:
                    line.ch_warehouse_qty = line.product_id.with_context(warehouse=ch_warehouse.id).free_qty

                if bv_warehouse:
                    line.bv_warehouse_qty = line.product_id.with_context(warehouse=bv_warehouse.id).free_qty

class purchase_order(models.Model):

    _inherit = "purchase.order"

    def button_confirm(self):
        """ Confirm the inter company sales order."""
        res = super(purchase_order, self).button_confirm()
        for order in self:
            if order.partner_ref and order.state=='purchase':
                sale_order = order.env['sale.order'].sudo().search([('name','=',order.partner_ref)],limit=1)
                if sale_order:
                    sale_order.with_company(sale_order.company_id).action_confirm()
        return res

    @api.model
    def action_create_and_post_bills(self):
        for purchase in self.env["purchase.order"].sudo().search([("invoice_status", "=", "to invoice"), ("state", "=", "purchase")]):
            try:
                with self.env.cr.savepoint():
                    # If receipt have sale order and purchase order in it, it means it's from intermediate purchase order so we need to create and confirm the purchase order
                    is_intercompany_purchase = purchase.picking_ids.filtered(lambda p: p.state == "done").mapped("sale_id")
                    if is_intercompany_purchase:
                        bill_id = purchase.action_create_invoice()
                        bill = self.env["account.move"].sudo().browse(bill_id.get("res_id", None))
                        if bill:
                            bill.write({'ref': "%s-%s" % (bill.ref, bill.id), "invoice_date": datetime.today()})
                            bill.action_post()
            except IntegrityError as e:
                _logger.error(f"Database error while creating bill for {purchase.name}: {e}")
            except Exception as e:
                _logger.error("Error while creating bill for %s: %s" % (purchase.name, e))


    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        invoice_vals = super(purchase_order,self)._prepare_invoice()
        invoice_vals.update({
            'partner_bank_id': self.partner_id.bank_ids[:1].filtered(lambda bank:bank.company_id.id == self.company_id.id).id,
        })

        return invoice_vals


class ProcurementGroup(models.Model):
    
    _inherit = 'procurement.group'


    def _get_product_routes(self,product_id):
        context = dict(self.env.context or {})
        if context and context.get('sale_order'):
            SaleOrder = context.get('sale_order')
            if SaleOrder and SaleOrder.auto_purchase_order_id:
                return product_id.route_ids.filtered(lambda route: route.company_id.id in [SaleOrder.company_id.id,False]) | product_id.categ_id.total_route_ids.filtered(lambda route: route.company_id.id in [SaleOrder.company_id.id,False])
            else:
                return product_id.route_ids | product_id.categ_id.total_route_ids
        else:
            return product_id.route_ids | product_id.categ_id.total_route_ids

    
    @api.model
    def _search_rule(self, route_ids, packaging_id, product_id, warehouse_id, domain):
        "override _search_rule method to get routes from original sale order"
        
        if warehouse_id:
            domain = expression.AND([['|', ('warehouse_id', '=', warehouse_id.id), ('warehouse_id', '=', False)], domain])
        Rule = self.env['stock.rule']
        res = self.env['stock.rule']
        if route_ids:
            res = Rule.search(expression.AND([[('route_id', 'in', route_ids.ids)], domain]), order='route_sequence, sequence', limit=1)
        if not res and packaging_id:
            packaging_routes = packaging_id.route_ids
            if packaging_routes:
                res = Rule.search(expression.AND([[('route_id', 'in', packaging_routes.ids)], domain]), order='route_sequence, sequence', limit=1)
        if not res:
            product_routes = self._get_product_routes(product_id)
            if product_routes:
                res = Rule.search(expression.AND([[('route_id', 'in', product_routes.ids)], domain]), order='route_sequence, sequence', limit=1)
        if not res and warehouse_id:
            warehouse_routes = warehouse_id.route_ids
            if warehouse_routes:
                res = Rule.search(expression.AND([[('route_id', 'in', warehouse_routes.ids)], domain]), order='route_sequence, sequence', limit=1)
        return res