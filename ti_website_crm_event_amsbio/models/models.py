# -*- coding: utf-8 -*-
import json
import base64
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.tools.json import scriptsafe as json_scriptsafe
import logging
_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = "crm.lead"

    intrest_ids = fields.Many2many("crm.tag", "main_intrest_lead_rel", "lead_id", "tag_id", string="Intrests", copy=False)
    sub_intrest_ids = fields.Many2many("crm.tag", "sub_intrest_lead_rel", "lead_id", "tag_id", string="Sub-Intrests", copy=False)
    mailing_list = fields.Boolean("Mailing list")
    amsbio_source = fields.Selection(
        [
            ("customer", "Existing Customer"),
            ("googlw", "Google Search/Google Ad"),
            ("human", "Colleague/Friend/Word of Mouth"),
            ("journal", "Journal Publication"),
            ("email", "Email Compaign"),
            ("web_print_ad", "Web or Print Advert"),
            ("socail_media", "Social Media (e.g. LinkedIn)"),
            ("other_web", "From other website"),
            ("other", "Other"),
            ("cant_recall", "Can't recall"),
        ],
        string="How did you hear about us?"
    )
    

class CrmTag(models.Model):
    _inherit = "crm.tag"

    parent_id = fields.Many2one("crm.tag", "Parent Tag", copy=False)
    child_ids = fields.One2many("crm.tag", "parent_id", "Childs Tags", copy=False)

    @api.constrains("parent_id")
    def _check_parent_id(self):
        for rec in self:
            if rec.parent_id and rec.parent_id == rec:
                raise ValidationError(_(f"Error! Parent and child can't be same."))

            
