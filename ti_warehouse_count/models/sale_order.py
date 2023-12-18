# -*-coding: utf-8 -*-

import logging
from datetime import timedelta
from psycopg2 import IntegrityError
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    _sql_constraints = [('customer_ref_partner_uniq', 'unique (client_order_ref,partner_id)', _('The Customer Reference must be unique per Customer!'))]


    delivery_time_week = fields.Integer('Delivery Time (Weeks)',default=1,copy=False)
    target_delivery_date = fields.Datetime(string='Target Delivery Date',copy=False,default=fields.Datetime.now() + timedelta(weeks= 1))
    intercompany_sale_order = fields.Char('Intercompany Sales Order')


    @api.onchange('delivery_time_week','date_order')
    def _onchange_target_delivery_date(self):
        for rec in self:
            rec.target_delivery_date = rec.date_order + timedelta(weeks= rec.delivery_time_week)


    def _action_confirm(self):
        self = self.with_context(sale_order=self)
        res = super(SaleOrder, self)._action_confirm()
        return res


    def action_confirm(self):
        result = super(SaleOrder, self).action_confirm()
        for order in self:
            purchase_order = order._get_purchase_orders()
            if not order.auto_purchase_order_id:
                if purchase_order and len(purchase_order)==1 and purchase_order.state!='purchase':
                    for line in order.order_line.sudo():
                        line = line.with_company(line.company_id)
                        if not line.product_id:
                            line.env['purchase.order.line'].sudo().create(order._prepare_vals_for_section_note(line, order.date_order, purchase_order))

            # We have to confirm all the intermediate purchase orders made for intercompany purchases
            companies_contacts = self.env["res.company"].sudo().search([]).mapped("partner_id")
            if purchase_order and purchase_order.partner_id in companies_contacts:
                purchase_order.button_confirm()
        return result


    def _prepare_vals_for_section_note(self, so_line, date_order,purchase_order):
        """ Generate purchase order line values, from the SO line
            :param so_line : origin SO line
            :rtype so_line : sale.order.line record
            :param date_order : the date of the orgin SO
        """
        return {
            'name': so_line.name,
            'product_qty': 0,
            'product_id': so_line.product_id and so_line.product_id.id or False,
            'product_uom': so_line.product_id and so_line.product_id.uom_po_id.id or so_line.product_uom.id,
            'price_unit': 0.0,
            'company_id': self.company_id.id,
            'date_planned': so_line.order_id.expected_date or date_order,
            'display_type': so_line.display_type,
            'order_id': purchase_order.id,
        }

    @api.model
    def action_create_and_post_invoices(self):
        for order in self.env["sale.order"].sudo().search([("invoice_status", "=", "to invoice"), ("state", "=", "sale")]):
            try:
                with self.env.cr.savepoint():
                    invoiceable_lines = order._get_invoiceable_lines(True)
                    if invoiceable_lines:
                        invoice = order._create_invoices(final=True)
                        if order.auto_purchase_order_id:
                            invoice.action_post()
            except IntegrityError as e:
                _logger.error(f"Database error while creating invoice for {order.name}: {e}")
            except Exception as e:
                _logger.error("Error while creating invoice for %s: %s" % (order.name, e))


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    uk_warehouse_qty = fields.Float('Available Qty For UK Warehouse', readonly=True, compute='_compute_warehouse_qty')
    uk_us_warehouse_qty = fields.Float('Available Qty For UK-US Warehouse', readonly=True, compute='_compute_warehouse_qty')
    ch_warehouse_qty = fields.Float('Available Qty For CH Warehouse', readonly=True, compute='_compute_warehouse_qty')
    bv_warehouse_qty = fields.Float('Available Qty For BV Warehouse', readonly=True, compute='_compute_warehouse_qty')


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
                    line.uk_warehouse_qty = line.product_id.with_context(warehouse=uk_warehouse.id).qty_available

                if us_warehouse:
                    line.uk_us_warehouse_qty = line.product_id.with_context(warehouse=us_warehouse.id).qty_available

                if ch_warehouse:
                    line.ch_warehouse_qty = line.product_id.with_context(warehouse=ch_warehouse.id).qty_available

                if bv_warehouse:
                    line.bv_warehouse_qty = line.product_id.with_context(warehouse=bv_warehouse.id).qty_available

    @api.model_create_multi
    def create(self, vals_list):
        "override create method to set route_id if not available in vals_list"

        lines = super(SaleOrderLine, self).create(vals_list)
        for line in lines.filtered(lambda sol: not sol.route_id and sol.product_id and sol.product_id.is_eu_supplier):
            route = line.order_id.company_id.route_id
            if route:
                line.write({'route_id': route.id})
        return lines