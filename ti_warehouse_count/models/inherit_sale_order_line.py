# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# https://support.targetintegration.com/issues/6728

from odoo.exceptions import UserError
from odoo import api, fields, models, _
from logging import getLogger
_logger = getLogger(__name__)



class ProductTemplate(models.Model):
    _inherit = 'product.template'


    is_vendor_updated = fields.Boolean('Is vendor updated',default=False)
    is_reordering_updated = fields.Boolean('Is reordering updated',default=False)


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



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

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


class SaleOrder(models.Model):
    _inherit = "sale.order"

    _sql_constraints = [('customer_ref_partner_uniq', 'unique (client_order_ref,partner_id)', _('The Customer Reference must be unique per Customer!'))]


    @api.onchange('delivery_time_week')
    def check_field_type(self):
        for rec in self:
            if rec.delivery_time_week and rec.delivery_time_week.strip()!="":
                try:
                    rec.delivery_time_week = int(rec.delivery_time_week.strip())
                except Exception as e:
                    raise UserError(_(f'Invalid Field Value.'))


    delivery_time_week = fields.Char('Delivery Time (Weeks)')


    def _action_confirm(self):
        result = super(SaleOrder, self)._action_confirm()
        for order in self:
            po = order._get_purchase_orders()
            if po and len(po)==1:
                po.button_confirm()
        return result