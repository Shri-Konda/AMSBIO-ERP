# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# https://support.targetintegration.com/issues/6728

from odoo.exceptions import UserError
from odoo import api, fields, models, SUPERUSER_ID,_
from datetime import datetime, timedelta
from logging import getLogger
_logger = getLogger(__name__)
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare



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
            if not order.auto_purchase_order_id:
                po = order._get_purchase_orders()
                if po and len(po)==1 and po.state!='purchase':
                    po.button_confirm()
        return result


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
