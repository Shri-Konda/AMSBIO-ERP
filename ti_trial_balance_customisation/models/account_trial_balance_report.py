# -*-coding: utf-8 -*-

import logging
from odoo import models, fields, _
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT


_logger = logging.getLogger(__name__)


class TrialBalanceCustomHandler(models.AbstractModel):
    _inherit = 'account.trial.balance.report.handler'
    
    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals):

        lines = super(TrialBalanceCustomHandler, self)._dynamic_lines_generator(report, options, all_column_groups_expression_totals)
        # _logger.info(f"\n==>lines: {lines}")
        new_lines = []
        for line in lines:
            balance_line = line[-1].copy()
            balance_columns = []
            columns = balance_line["columns"]
            for i in range(0, len(columns), 2):
                debit = columns[i]
                credit = columns[i+1] if i+1 < len(columns) else {}
                # _logger.info(f"\n{balance_line.get('name')} ==>debit: {debit} ==>credit: {credit}")
                balance = debit.get("no_format", 0.0) - credit.get("no_format", 0.0)
                # _logger.info(f"\n==>debit: {debit.get('no_format', 0.0)} ==>credit: {credit.get('no_format', 0.0)} ==>balance: {balance}")
                balance_columns.append({'name': self.env['account.report'].format_value(balance, figure_type='monetary'), 'no_format': balance, 'class': "number"})
            balance_line["columns"] = balance_columns
            new_lines.append((0, balance_line))
        # _logger.info(f"\n==>new_lines: {new_lines}")

        new_columns = []
        # instead of debit/credit columns add a single column for balance
        if options['columns']:
            for i in range(0, len(options['columns']), 2):
                debit = options['columns'][i]
                balance_column = debit.copy()
                balance_column.update({'name': _("Balance")})
                new_columns.append(balance_column)

        # _logger.info(f"\n==>new_columns: {new_columns}")
        options['columns'] = new_columns
        return new_lines
