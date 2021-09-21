# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _
from logging import getLogger
_logger = getLogger(__name__)

class Product(models.Model):
    _inherit = "product.product"


    def _get_available_qty(self,warehouse):
        location_ids = warehouse.mapped('view_location_id').ids
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations_new(location_ids, compute_child=self.env.context.get('compute_child', True))
        domain_quant = [('product_id', 'in', self.ids)] + domain_quant_loc          
        Quant = self.env['stock.quant'].with_context(active_test=False)
        quants_res = Quant.search(domain_quant).mapped('available_quantity',)

        if quants_res:
            return quants_res[0]
        return 0




class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    uk_warehouse_qty = fields.Float('Available Qty in UK Warehouse', readonly=True, compute='_compute_warehouse_qty')
    uk_us_warehouse_qty = fields.Float('Available Qty in UK-US Warehouse', readonly=True, compute='_compute_warehouse_qty')


    @api.depends('product_id')
    def _compute_warehouse_qty(self):
        for line in self:
            if line.company_id.name =='AMS Biotechnology (Europe) Limited':
                warehouses = self.env['stock.warehouse'].sudo().search([("company_id","=",line.company_id.id)])
                
                if len(warehouses)==2:
                    line.uk_warehouse_qty = line.product_id._get_available_qty(warehouse=warehouses[0])
                    line.uk_us_warehouse_qty = line.product_id._get_available_qty(warehouse=warehouses[1])
                else:
                    line.uk_warehouse_qty = 0
                    line.uk_us_warehouse_qty = 0
            else:
                    line.uk_warehouse_qty = 0
                    line.uk_us_warehouse_qty = 0



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    uk_warehouse_qty = fields.Float('Available Qty in UK Warehouse', readonly=True, compute='_compute_warehouse_qty')
    uk_us_warehouse_qty = fields.Float('Available Qty in UK-US Warehouse', readonly=True, compute='_compute_warehouse_qty')


    @api.depends('product_id')
    def _compute_warehouse_qty(self):
        for line in self:
            if line.company_id.name=='AMS Biotechnology (Europe) Limited':
                warehouses = self.env['stock.warehouse'].sudo().search([("company_id","=",line.company_id.id)])
                if len(warehouses)==2:
                    line.uk_warehouse_qty = line.product_id._get_available_qty(warehouse=warehouses[0])
                    line.uk_us_warehouse_qty = line.product_id._get_available_qty(warehouse=warehouses[1])
                else:
                    line.uk_warehouse_qty = 0
                    line.uk_us_warehouse_qty = 0
            else:
                    line.uk_warehouse_qty = 0
                    line.uk_us_warehouse_qty = 0

