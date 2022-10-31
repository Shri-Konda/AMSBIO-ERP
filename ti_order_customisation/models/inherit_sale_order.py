# -*-coding: utf-8 -*-

from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_id = fields.Many2one(domain="[('is_company', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")