# -*-coding: utf-8 -*-

import re
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

class BankStatementImportTemplate(models.Model):
    _name = "bank.statement.import.custom.template"
    _description = "Bank Statement Import Custom Template"

    name = fields.Char(string="Bank Name", required=True)
    separator = fields.Selection(selection=[(',', ","), (';', ";")], string="CSV Separator", default=",", required=True)
    row_offset = fields.Integer("Data Starts From", default=1, help="In case file has extra information in first few rows, exclude these many rows")
    template_line_ids = fields.One2many(comodel_name="bank.statement.import.custom.template.line", inverse_name="template_id")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, required=True)


class BankStatementImportTemplateLine(models.Model):
    _name = "bank.statement.import.custom.template.line"
    _description = "Bank Statement Import Custom Template Line"

    def _template_line_field_domain(self):
        statement_line_model = self.env["ir.model"].sudo().search([('model', '=', "account.bank.statement.line")], limit=1)
        return [('model_id', '=', statement_line_model.id)]

    template_id = fields.Many2one("bank.statement.import.custom.template", ondelete="cascade")
    column_name = fields.Char(string="Column Name", required=True)
    column_index = fields.Char(string="Column Index", required=True)

    def _get_formatted_value(self, row, index):
        "check and format the value and return it"

        # check for multiple indicies, then we need to contactinate the values
        if "+" in index:
            indices = index.strip().split("+")
            value = " ".join([row[int(i)] for i in indices])
        else:
            value = row[int(index)]

        # check if the value is monetary, then only format it as money
        if self.column_name.lower() in ["credit", "debit"]:
            # remove negative sign from value
            value = value.replace("-", '')
            value = value.replace(",", '')
            value = value.replace("'", '')

            # create regular expression based whether monetary sign is available or not
            if value.startswith("$"):
                pattern = r'\$\d+\.\d{2}'
            else:
                pattern = r'\d+\.\d{2}'
            match = re.search(pattern, value)
            if match:
                value = match.group(0)
        if self.column_name.lower() in ["date"]:
            value = value.replace(".", "/")
        return value