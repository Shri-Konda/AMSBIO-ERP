# -*-coding: utf-8 -*-

import logging
from odoo import models

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"


    def action_view_sale_order(self):
        "override method to remove default partner when creating SO from smart button"

        action = super(Partner, self).action_view_sale_order()
        context = {}
        if self.is_company:
            context["default_partner_id"] = self.id
        elif self.parent_id:
            context["default_partner_id"] = self.parent_id.id
        elif self.type == "contact":
            context["default_partner_id"] = self.id
        else:
            context["default_partner_id"] = False
        action["context"] = str(context)
        return action