# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from logging import getLogger
_logger = getLogger(__name__)


class IrExports(models.Model):
    _inherit = "ir.exports"
    

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        res =  super(IrExports, self).search_read(domain, fields, offset, limit, order)
        if self.env.user.user_has_groups('ti_export_group_customization.ti_delete_export_template'):
            res.append({
                'id'  : -1,
                'hide_delete_button': True,  
            })
        else:
            res.append({
                'id'  : -1,
                'hide_delete_button': False,  
            })

        return res