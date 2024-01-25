# -*-coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError


class MRPOrder(models.Model):
    _inherit = "mrp.production"

    def button_mark_done(self):
        "override method to raise error if components are not available"

        for order in self:
            if order.components_availability_state != "available":
                raise UserError(_("You cannot mark the order done when components are not available!"))

        return super(MRPOrder, self).button_mark_done()
