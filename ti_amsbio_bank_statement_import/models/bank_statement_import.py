# -*-coding: utf-8 -*-

import csv
import logging
from odoo import models, fields, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

class AccountBankStatementImport(models.TransientModel):
    _inherit = "account.bank.statement.import"

    def _default_custom_template_id(self):
        custom_template = self.env["bank.statement.import.custom.template"].search([("company_id", 'in', self.env.company.ids)], limit=1)
        return custom_template

    use_custom_template = fields.Boolean(default=False, string="Use Custom Template?")
    custom_template_id = fields.Many2one("bank.statement.import.custom.template", help="Use this custom template to format csv file before importing.", default=_default_custom_template_id)

    def import_file(self):
        "override original method to use custom template for import bank statements"

        # In case of CSV files, only one file can be imported at a time.
        if len(self.attachment_ids) > 1:
            csv = [bool(self._check_csv(att.name)) for att in self.attachment_ids]
            if True in csv and False in csv:
                raise UserError(_('Mixing CSV files with other file types is not allowed.'))
            if csv.count(True) > 1:
                raise UserError(_('Only one CSV file can be selected.'))
            return super(AccountBankStatementImport, self).import_file()

        if not self._check_csv(self.attachment_ids.name):
            return super(AccountBankStatementImport, self).import_file()

        if self.use_custom_template and self.custom_template_id:
            return self._format_and_import_bank_statement(self.custom_template_id, self.attachment_ids)
        else:
            return super(AccountBankStatementImport, self).import_file()


    def _format_and_import_bank_statement(self, custom_template, attachment_id):
        "format the custom template to make it importable in Odoo"

        parsed_data = ""
        # adding header/field name of Odoo from custom template
        if custom_template.template_line_ids:
            parsed_data += ";".join([line.column_name for line in custom_template.template_line_ids]) + "\n"

        # get data from attachment and parse them
        csv_data = attachment_id.index_content
        lines = csv_data.splitlines()
        # _logger.info(f"\n==>lines: {lines}")
        if lines:
            # check for the delimiter of the file
            separator = custom_template.separator
            reader = csv.reader(lines, delimiter=separator)

            # excludes rows which contains extra informations
            if custom_template.row_offset:
                for i in range(custom_template.row_offset):
                    next(reader)

            for row in reader:
                has_debit_or_credit = False
                # _logger.info(f"\n==>row: {row}")
                for column in custom_template.template_line_ids:
                    if column.column_name.lower() in ["debit", "credit"] and row[int(column.column_index)]:
                        has_debit_or_credit = True
                        break
                if has_debit_or_credit:
                    values = [line._get_formatted_value(row, line.column_index) for line in custom_template.template_line_ids]
                    parsed_data += ";".join(values) + "\n"
                # _logger.info(f"\n{row} ==> {values}")

        # create import wizard with the data
        import_wizard = self.env['base_import.import'].create({
            'res_model': 'account.bank.statement.line',
            'file': parsed_data.encode(),
            'file_name': attachment_id.name,
            'file_type': 'text/csv'
        })

        ctx = dict(self.env.context)
        ctx['wizard_id'] = import_wizard.id
        return {
            'type': 'ir.actions.client',
            'tag': 'import_bank_stmt',
            'params': {
                'model': 'account.bank.statement.line',
                'context': ctx,
                'filename': attachment_id.name,
            }
        }

