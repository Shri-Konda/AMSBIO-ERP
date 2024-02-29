# -*-coding: utf-8 -*-

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    amsbio_edi_account_number = fields.Char("EDI Account Number", readonly=True, copy=False, help="Unique account number for the customer whose orders are created through EDI integration.")
    street3 = fields.Char(string="Street 3")
    fisher_street = fields.Char(string="Fisher Address Street", readonly=True, copy=False)
    fisher_street2 = fields.Char(string="Fisher Address Street2", readonly=True, copy=False)
    fisher_city = fields.Char(string="Fisher Address City", readonly=True, copy=False)
    fisher_state = fields.Char(string="Fisher Address State", readonly=True, copy=False)
    fisher_zip = fields.Char(string="Fisher Address ZIP", readonly=True, copy=False)

    @api.model
    def _formatting_address_fields(self):
        "override method to add street3 on the format"

        address_format = super(Partner, self)._formatting_address_fields()
        if address_format:
            address_format.append("street3")

        return address_format
    
    @api.model
    def _get_address_format(self):
        "override mthod to add street3 on the format"
        
        address_format = super(Partner, self)._get_address_format()
        if address_format:
            return address_format.replace("%(street2)s", "%(street2)s\n%(street3)s")
        return address_format