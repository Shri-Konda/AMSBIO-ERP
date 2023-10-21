# -*-coding: utf-8 -*-

import logging
from odoo import models

_logger = logging.getLogger(__name__)

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, name, amount, so_line):
        "Override method to pass edi information to invoice if related sale order was created through EDI integration."

        invoice_vals = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, name, amount, so_line)
        if order.ftp_server_id:
            invoice_vals.update({'ftp_server_id': order.ftp_server_id.id})
        _logger.info(f"\n==>wizard invoice_vals: {invoice_vals}")
        return invoice_vals