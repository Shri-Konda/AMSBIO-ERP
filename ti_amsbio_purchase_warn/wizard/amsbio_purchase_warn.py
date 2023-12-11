# -*-coding: utf-8 -*-

from odoo import models, fields

class AMSBIOPurchaseWarn(models.Model):
    _name = "amsbio.purchase.warn"
    _description = "AMSBIO Purchase Warning"

    purchase_order_id = fields.Many2one(comodel_name="purchase.order", string="Purchase Order", required=True)
    purchase_partner_id = fields.Many2one(related="purchase_order_id.partner_id", required=True)
    purchase_warn = fields.Selection(related="purchase_partner_id.purchase_warn")
    purchase_warn_msg = fields.Text(related="purchase_partner_id.purchase_warn_msg")

    def action_confirm(self):
        return self.purchase_order_id.with_context(skip_purchase_warn=True).button_confirm()
