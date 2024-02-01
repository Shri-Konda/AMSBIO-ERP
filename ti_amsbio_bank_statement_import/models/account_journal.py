# -*-coding: utf-8 -*-

import csv
import logging
from odoo import models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = "account.journal"

    custom_import_template_id = fields.Many2one("bank.statement.import.custom.template", check_company=True, copy=False, string="Custom Import Template", help="Select the custom csv template which will be used to format data from import csv.")

    def _import_bank_statement(self, attachments):
        "override the method to format data using custom import template before adding for import"

        # In case of CSV files, only one file can be imported at a time.
        if len(attachments) > 1:
            csv = [bool(self._check_csv(att.name)) for att in attachments]
            if True in csv and False in csv:
                raise UserError(_('Mixing CSV files with other file types is not allowed.'))
            if csv.count(True) > 1:
                raise UserError(_('Only one CSV file can be selected.'))
            return super()._import_bank_statement(attachments)

        if not self._check_csv(attachments.name):
            return super()._import_bank_statement(attachments)

        # If custom import template is selected, then format data before importing
        if self.custom_import_template_id:
            return self._format_and_import_bank_statement(attachments)

        return super(AccountJournal, self)._import_bank_statement(attachments)

    def _format_and_import_bank_statement(self, attachment):
        "format the custom template to make it importable in Odoo"

        parsed_data = ""
        parsed_vals = []
        custom_template = self.custom_import_template_id
        # adding header/field name of Odoo from custom template
        if custom_template.template_line_ids:
            parsed_data += ";".join([line.column_name for line in custom_template.template_line_ids]) + "\n"

        # get data from attachment and parse them
        csv_data = attachment.index_content
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
                    parsed_vals.append(values)

        # sort the data by date as Odoo requires sorted data
        parsed_vals.sort(key=lambda l: l[0])
        for vals in parsed_vals:
            parsed_data += ";".join(vals) + "\n"

        # create import wizard with the data
        import_wizard = self.env['base_import.import'].create({
            'res_model': 'account.bank.statement.line',
            'file': parsed_data.encode(),
            'file_name': attachment.name,
            'file_type': 'text/csv'
        })

        ctx = dict(self.env.context)
        ctx['wizard_id'] = import_wizard.id
        ctx['default_journal_id'] = self.id
        return {
            'type': 'ir.actions.client',
            'tag': 'import_bank_stmt',
            'params': {
                'model': 'account.bank.statement.line',
                'context': ctx,
                'filename': 'bank_statement_import.csv',
            }
        }