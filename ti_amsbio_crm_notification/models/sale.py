# -*-coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import models, api, fields, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _cron_execute_followup(self):
        "override method to pass in context that followup is done through cron"


        for company in self.env["res.company"].search([]):
            # Since the cache is done by database and not by company, we need to invalidate in this special case
            # where the context is changing in the same transaction
            self.env.cr.execute("DROP TABLE IF EXISTS followup_data_cache")
            self.with_context(allowed_company_ids=company.ids, followup_from_cron=True)._cron_execute_followup_company()

    def _get_followup_responsible(self):
        "override method to return responsible user"

        self.ensure_one()
        if self._context.get("followup_from_cron", False):
            return super(ResPartner, self)._get_followup_responsible()
        else:
            return self.env.user