# -*-coding: utf-8 -*-

from . import models
from . import wizard

from odoo import api, SUPERUSER_ID, _
from odoo.exceptions import UserError

def pre_init_amsbio_edi(cr):
    """check if studio fields used in integration are created"""

    env = api.Environment(cr, SUPERUSER_ID, {})
    fax = env["ir.model.fields"].search([('model_id.model', '=', 'res.partner'), ("name", "=", "x_studio_fax")], limit=1)
    if not fax:
        raise UserError(_("'x_studio_fax' field on contact is used in the Integration which is not available. Please create it for Integration to work properly."))