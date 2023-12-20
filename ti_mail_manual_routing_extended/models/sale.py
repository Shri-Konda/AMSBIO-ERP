# -*-coding: utf-8 -*-

from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    amsbio_previous_conversation = fields.Text(string="Previous Conversation", readonly=False)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    amsbio_previous_conversation = fields.Text(string="Previous Conversation", readonly=False)

class CrmLead(models.Model):
    _inherit = "crm.lead"

    amsbio_previous_conversation = fields.Text(string="Previous Conversation", readonly=False)