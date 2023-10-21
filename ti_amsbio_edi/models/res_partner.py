# -*-coding: utf-8 -*-

from odoo import models, fields


class Partner(models.Model):
    _inherit = "res.partner"

    amsbio_edi_account_number = fields.Char("EDI Account Number", readonly=True, copy=False, help="Unique account number for the customer whose orders are created through EDI integration.")