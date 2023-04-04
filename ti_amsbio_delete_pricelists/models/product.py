# -*-coding: utf-8 -*-

import logging
from odoo import models

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_archive(self):
        "override method to delete all the associated pricelists when product is archived"

        for product in self:
            sales_pricelists = self.env["product.pricelist.item"].sudo().search([("product_tmpl_id", "=", product.id)])
            vendor_pricelists = self.env["product.supplierinfo"].sudo().search([("product_tmpl_id", "=", product.id)])
            # _logger.info(f"\n==>product: {product.name}\n==>sales_pricelists: {sales_pricelists}\n==>vendor_pricelists: {vendor_pricelists}")
            sales_pricelists.unlink()
            vendor_pricelists.unlink()

        return super(ProductTemplate, self).action_archive()
    
class ProductVariant(models.Model):
    _inherit = "product.product"

    def action_archive(self):
        "override method to delete all the associated pricelists when product is archived"

        for product in self:
            sales_pricelists = self.env["product.pricelist.item"].sudo().search(['|', ("product_id", "=", product.id), '&', ('product_id', '=', False), ('product_tmpl_id', '=', product.product_tmpl_id.id)])
            vendor_pricelists = self.env["product.supplierinfo"].sudo().search(['|', ("product_id", "=", product.id), '&', ('product_id', '=', False), ('product_tmpl_id', '=', product.product_tmpl_id.id)])
            # _logger.info(f"\n==>product variant: {product.name}\n==>sales_pricelists: {sales_pricelists}\n==>vendor_pricelists: {vendor_pricelists}")
            sales_pricelists.unlink()
            vendor_pricelists.unlink()
        return super(ProductVariant, self).action_archive()