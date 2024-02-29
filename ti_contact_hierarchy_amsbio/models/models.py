# -*- coding: utf-8 -*-
import json
import base64
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.tools.json import scriptsafe as json_scriptsafe
import logging
_logger = logging.getLogger(__name__)


class Contact(models.Model):
    _inherit = "res.partner"

    company_type = fields.Selection(selection_add=[('department', 'Department')], compute='_compute_company_type', inverse='_write_company_type')
    is_department = fields.Boolean(string='Is a Department', default=False,
        help="Check if the contact is a department")

    @api.depends('is_company', 'is_department')
    def _compute_company_type(self):
        for partner in self:
            partner.company_type = 'company' if partner.is_company else 'department' if partner.is_department else 'person'

    def _write_company_type(self):
        for partner in self:
            partner.is_company = partner.company_type == 'company'
            partner.is_department = partner.company_type == 'department'

    @api.onchange('company_type')
    def onchange_company_type(self):
        if self.company_type == 'company':
            self.is_company = True
            self.is_department = False
        elif self.company_type == 'department':
            self.is_department = True
            self.is_company = False
        else:
            self.is_company = False
            self.is_department = False

