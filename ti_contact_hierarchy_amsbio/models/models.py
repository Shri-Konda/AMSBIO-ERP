# -*- coding: utf-8 -*-
import json
import base64
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.tools.json import scriptsafe as json_scriptsafe
import logging
_logger = logging.getLogger(__name__)

class ContactDepartment(models.Model):
    _name = "contact.department"

    name = fields.Char("Name", required=True, copy=False)
    contact_id = fields.Many2one("res.partner", string="Company", doamin="[('is_company', '=', True)]")

    

class Contact(models.Model):
    _inherit = "res.partner"

    # company type contact will have multiple it's own departments
    contact_department_ids = fields.One2many("contact.department", "contact_id", string="Departments")

    # company child contact has many2one field so that we can identify each child relate to which department
    conatc_department_id = fields.Many2one("contact.department", string="Department")

