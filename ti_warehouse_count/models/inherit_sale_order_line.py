# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# https://support.targetintegration.com/issues/6728

from odoo.exceptions import UserError
from odoo import api, fields, models, SUPERUSER_ID,_
from datetime import datetime, timedelta, time
from logging import getLogger
_logger = getLogger(__name__)
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from psycopg2 import IntegrityError
from odoo.tools.float_utils import float_round



class ProductTemplate(models.Model):
    _inherit = 'product.template'


    is_vendor_updated = fields.Boolean('Is vendor updated',default=False)
    is_reordering_updated = fields.Boolean('Is reordering updated',default=False)

    is_eu_supplier = fields.Boolean('Is EU Supplier',default=False)


class Product(models.Model):
    _inherit = "product.product"


    def _get_available_qty(self,warehouse):
        location_ids = warehouse.mapped('view_location_id').ids
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations_new(location_ids, compute_child=self.env.context.get('compute_child', True))
        domain_quant = [('product_id', 'in', self.ids)] + domain_quant_loc          
        Quant = self.env['stock.quant'].with_context(active_test=False)
        quants_res = Quant.search(domain_quant).mapped('available_quantity',)

        if quants_res:
            return sum(quants_res)
        return 0

    def _compute_sales_count(self):
        "Overriding the defaul method to avoid the checking of salesman group."
        
        r = {}
        self.sales_count = 0
        date_from = fields.Datetime.to_string(fields.datetime.combine(fields.datetime.now() - timedelta(days=365),
                                                                      time.min))

        done_states = self.env['sale.report']._get_done_states()
        domain = [
            ('state', 'in', done_states),
            ('product_id', 'in', self.ids),
            ('date', '>=', date_from),
        ]
        for group in self.env['sale.report'].read_group(domain, ['product_id', 'product_uom_qty'], ['product_id']):
            r[group['product_id'][0]] = group['product_uom_qty']
        for product in self:
            if not product.id:
                product.sales_count = 0.0
                continue
            product.sales_count = float_round(r.get(product.id, 0), precision_rounding=product.uom_id.rounding)
        return r




class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    uk_warehouse_qty = fields.Float('Available Qty For UK Warehouse', readonly=True, compute='_compute_warehouse_qty')
    uk_us_warehouse_qty = fields.Float('Available Qty For UK-US Warehouse', readonly=True, compute='_compute_warehouse_qty')
    ch_warehouse_qty = fields.Float('Available Qty For CH Warehouse', readonly=True, compute='_compute_warehouse_qty')
    bv_warehouse_qty = fields.Float('Available Qty For BV Warehouse', readonly=True, compute='_compute_warehouse_qty')


    @api.depends('product_id')
    def _compute_warehouse_qty(self):
        for line in self:
            IrDefault = self.env['ir.default'].sudo()
            company_id = IrDefault.get('res.config.settings', 'warehouse_count')
            company_id = self.env['res.company'].sudo().browse([company_id])
            if company_id and line.company_id.id == company_id.id:
                warehouses = self.env['stock.warehouse'].sudo().search([("company_id","=",line.company_id.id)])
                if len(warehouses)==4:
                    line.uk_warehouse_qty = line.product_id._get_available_qty(warehouse=warehouses[0])
                    line.uk_us_warehouse_qty = line.product_id._get_available_qty(warehouse=warehouses[1])
                    line.ch_warehouse_qty = line.product_id._get_available_qty(warehouse=warehouses[2])
                    line.bv_warehouse_qty = line.product_id._get_available_qty(warehouse=warehouses[3])
                else:
                    line.uk_warehouse_qty = 0
                    line.uk_us_warehouse_qty = 0
                    line.ch_warehouse_qty = 0
                    line.bv_warehouse_qty = 0
            else:
                    line.uk_warehouse_qty = 0
                    line.uk_us_warehouse_qty = 0
                    line.ch_warehouse_qty = 0
                    line.bv_warehouse_qty = 0


    @api.onchange('product_id')
    def product_id_change(self):
        result = super(SaleOrderLine, self).product_id_change()
        if self.product_id and self.product_id.is_eu_supplier:
            self.route_id = self.order_id.company_id.route_id and self.order_id.company_id.route_id.id
        return result

    @api.model
    def _prepare_add_missing_fields(self, values):
        """Override the default method to include route_id in onchange fields which will be computed based on cange of product_id."""

        res = {}
        onchange_fields = ['name', 'price_unit', 'product_uom', 'tax_id', 'route_id']
        if values.get('order_id') and values.get('product_id') and any(f not in values for f in onchange_fields):
            line = self.new(values)
            line.product_id_change()
            for field in onchange_fields:
                if field not in values:
                    res[field] = line._fields[field].convert_to_write(line[field], line)
        return res



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
            IrDefault = self.env['ir.default'].sudo()
            company_id = IrDefault.get('res.config.settings', 'warehouse_count')
            company_id = self.env['res.company'].sudo().browse([company_id])
            if company_id and line.company_id.id == company_id.id:
                warehouses = self.env['stock.warehouse'].sudo().search([("company_id","=",line.company_id.id)])
                if len(warehouses)==4:
                    line.uk_warehouse_qty = line.product_id._get_available_qty(warehouse=warehouses[0])
                    line.uk_us_warehouse_qty = line.product_id._get_available_qty(warehouse=warehouses[1])
                    line.ch_warehouse_qty = line.product_id._get_available_qty(warehouse=warehouses[2])
                    line.bv_warehouse_qty = line.product_id._get_available_qty(warehouse=warehouses[3])
                else:
                    line.uk_warehouse_qty = 0
                    line.uk_us_warehouse_qty = 0
                    line.ch_warehouse_qty = 0
                    line.bv_warehouse_qty = 0
            else:
                    line.uk_warehouse_qty = 0
                    line.uk_us_warehouse_qty = 0
                    line.ch_warehouse_qty = 0
                    line.bv_warehouse_qty = 0


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
            _logger.info(f"\n==>purchase order {purchase_order.name} for {order.name}\n")
            if not order.auto_purchase_order_id:
                if purchase_order and len(purchase_order)==1 and purchase_order.state!='purchase':
                    for line in order.order_line.sudo():
                        line = line.with_company(line.company_id)
                        if not line.product_id:
                            line.env['purchase.order.line'].sudo().create(order._prepare_po_line_data(line, order.date_order, purchase_order))

            # We have to confirm all the intermediate purchase orders made for intercompany purchases
            companies_contacts = self.env["res.company"].sudo().search([]).mapped("partner_id")
            _logger.info(f"\n==>Company Contacts: {companies_contacts.mapped('name')}\n==>supplier: {purchase_order and purchase_order.partner_id.name}\n")
            if purchase_order and purchase_order.partner_id in companies_contacts:
                purchase_order.button_confirm()
        return result


    def _prepare_po_line_data(self, so_line, date_order,purchase_order):
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
    def _search_rule(self, route_ids, product_id, warehouse_id, domain):
        """ First find a rule among the ones defined on the procurement
        group, then try on the routes defined for the product, finally fallback
        on the default behavior
        """
        if warehouse_id:
            domain = expression.AND([['|', ('warehouse_id', '=', warehouse_id.id), ('warehouse_id', '=', False)], domain])
        Rule = self.env['stock.rule']
        res = self.env['stock.rule']
        if route_ids:
            res = Rule.search(expression.AND([[('route_id', 'in', route_ids.ids)], domain]), order='route_sequence, sequence', limit=1)
        if not res:
            product_routes = self._get_product_routes(product_id)
            if product_routes:
                res = Rule.search(expression.AND([[('route_id', 'in', product_routes.ids)], domain]), order='route_sequence, sequence', limit=1)
        if not res and warehouse_id:
            warehouse_routes = warehouse_id.route_ids
            if warehouse_routes:
                res = Rule.search(expression.AND([[('route_id', 'in', warehouse_routes.ids)], domain]), order='route_sequence, sequence', limit=1)
        return res
