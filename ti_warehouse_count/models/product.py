# -*-coding: utf-8 -*-

from datetime import timedelta, time
from odoo import models, fields
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
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations_new(location_ids)
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
        date_from = fields.Datetime.to_string(fields.datetime.combine(fields.datetime.now() - timedelta(days=365), time.min))

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