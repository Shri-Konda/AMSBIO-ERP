# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from logging import getLogger
from odoo import models, api


_logger = getLogger(__name__)


class IrExports(models.Model):
    _inherit = "ir.exports"

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        "override method to flag whether user has right to delete export template or not"

        res =  super(IrExports, self).search_read(domain, fields, offset, limit, order)
        if self.env.user.user_has_groups('ti_export_group_customization.ti_delete_export_template'):
            # adding a pseudo record which will be used as flag
            res.append({"id": -1, "show_delete_button": True})
        return res