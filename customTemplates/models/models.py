# -*- coding: utf-8 -*-

from odoo import models, fields, api


class customTemplates(models.Model):
    _name = 'customTemplates.customTemplates'
    _inherit = 'sale.order'
