# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from ast import literal_eval

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    warehouse_count = fields.Many2one('res.company',string='Warehouse stock count',)
    vendor_pricelist_company_ids = fields.Many2many('res.company',string='Vendor Pricelist Companies')
    vendor_pricelist_partner_company = fields.Many2one('res.company',string='Vendor Pricelist Partner Company',)
    reordering_rule = fields.Many2one('res.company',string='Reordering Rule company',)


    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrDefault = self.env['ir.default'].sudo()
        IrDefault.set('res.config.settings', 'warehouse_count', self.warehouse_count.id)
        IrDefault.set('res.config.settings', 'reordering_rule', self.reordering_rule.id)
        IrDefault.set('res.config.settings', 'vendor_pricelist_partner_company', self.vendor_pricelist_partner_company.id)
        IrDefault.set('res.config.settings', 'vendor_pricelist_company_ids', self.vendor_pricelist_company_ids.ids)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrDefault = self.env['ir.default'].sudo()
        vendor_pricelist_company_ids = IrDefault.get('res.config.settings', 'vendor_pricelist_company_ids')
        res.update(
                warehouse_count = IrDefault.get('res.config.settings', 'warehouse_count'),
                reordering_rule = IrDefault.get('res.config.settings', 'reordering_rule'),
                vendor_pricelist_partner_company = IrDefault.get('res.config.settings', 'vendor_pricelist_partner_company'),
                # vendor_pricelist_company_ids = [(6,0,vendor_pricelist_company_ids)],
                )
        return res