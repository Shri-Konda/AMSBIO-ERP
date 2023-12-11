# -*-coding: utf-8 -*-

from odoo import models, _

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        "override method to raise warning for supplier"

        for order in self:
            partner = order.partner_id
            if not partner or order.env.user._is_superuser() or order._context.get("skip_purchase_warn", False) or partner.purchase_warn == "no-message":
                return super(PurchaseOrder, order).button_confirm()
            
            return {
                'name': _("Supplier Warning"),
                'type': "ir.actions.act_window",
                'view_mode': "form",
                'target': "new",
                'view_id': self.env.ref("ti_amsbio_purchase_warn.amsbio_purchase_warn_view_form").id,
                'res_model': "amsbio.purchase.warn",
                'context': {**order._context, 'default_purchase_order_id': order.id}
            }