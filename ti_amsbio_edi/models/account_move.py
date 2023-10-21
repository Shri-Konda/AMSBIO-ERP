# -*-coding: utf-8 -*-

import csv
import logging
from odoo.tools import format_date
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    sent_to_edi = fields.Boolean(string="Sent To EDI", default=False, readonly=True, copy=False, help="True if csv file for invoice is sent to FTP server")
    ftp_server_id = fields.Many2one("ftp.server", string="FTP Server", readonly=True, help="If invoice is for Order created through FTP server, then stores FTP server through which order was created.")

    @api.model
    def cron_edi_export_invoices(self):
        "Create csv file and send to FTP for invoices which were created for EDI orders"

        ftp_servers = self.env["ftp.server"]._get_ftp_servers()
        _logger.info(f"\n==>ftp_servers: {ftp_servers}")
        for server in ftp_servers:
            domain = [
                ('move_type', '=', "out_invoice"),
                ('company_id', '=', server.company_id.id),
                ('ftp_server_id', '=', server.id),
                ('state', '=', "posted"),
                ('sent_to_edi', '=', False),
            ]
            invoices_to_send = self.sudo().search(domain)
            _logger.info(f"\n==>invoices_to_send: {invoices_to_send}")

            invoices_export_folder = server.get_export_invoices_folder()
            for invoice in invoices_to_send:
                try:
                    invoice._create_edi_invoice_csv(invoices_export_folder)
                    invoice.write({'sent_to_edi': True})
                except Exception as e:
                    msg = "Error while creating EDI csv: <strong>%s</strong>" % e
                    _logger.error(f"\n==>{msg}")
                    invoice.message_post(body=_(msg))

            # onces files are created, send csv files to FTP server
            upload_to = server.ftp_invoice_location
            server.send_files_to_ftp(invoices_export_folder, upload_to)

    def _create_edi_invoice_csv(self, invoices_export_folder):
        "Prepare and create EDI csv file"

        self.ensure_one()
        invoice_csv_values = self._prepare_edi_invoice_values()
        if invoice_csv_values:
            filepath = f"{invoices_export_folder}/INV_{self.name.replace('/', '_')}.csv"
            with open(filepath, "w") as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerows(invoice_csv_values)

            # create attachment and post messages to invoice
            attachment = self.env["ftp.server"].create_file_attachment(filepath)
            attachment.write({'res_model': "account.move", 'res_id': self.id})
            msg = "Successfully created invoice csv file for EDI. Please find attached the csv."
            self.message_post(body=_(msg), attachment_ids=attachment.ids)

    def _prepare_edi_invoice_values(self):
        "Discuss with steffy about the info and format of data and update values"

        self.ensure_one()
        header = [
            "Order No.",
            "Customer Account Number",
            "Invoice Address Street",
            "Invoice Address Street2",
            "Invoice Address City",
            "Invoice Address State",
            "Invoice Address Zip",
            "Invoice Address Country",
            "Invoice Address Phone",
            "Invoice Address Email",
            "Delivery Address Street",
            "Delivery Address Street2",
            "Delivery Address City",
            "Delivery Address State",
            "Delivery Address Zip",
            "Delivery Address Country",
            "Delivery Address Phone",
            "Delivery Address Email",
            "Invoice Number",
            "Invoice Date",
            "Customer Purchase Order Number",
            "Customer Reference",
            "Currency",
            "Invoice Total",
            "Order Line Number",
            "Code",
            "Charges Code",
            "Description",
            "Origin Country",
            "Quantity",
            "UoM",
            "Unit Price",
            "Discount(%)",
            "Discount Value",
            "Amount with Discount before Tax",
            "Tax Code",
            "Sales Taxes",
            "Tax Percentage",
            "Amount after Tax without Discount",
            "Tariff Code",
            "Amount(with Tax and Discount)"
        ]

        values = [header]
        invoice_values = [
            self.invoice_origin or "",
            self.partner_shipping_id.amsbio_edi_account_number or "",
            self.partner_id.street or "",
            self.partner_id.street2 or "",
            self.partner_id.city or "",
            self.partner_id.state_id.display_name or "",
            self.partner_id.zip or "",
            self.partner_id.country_id.name or "",
            self.partner_id.phone or "",
            self.partner_id.email or "",
            self.partner_shipping_id.street or "",
            self.partner_shipping_id.street2 or "",
            self.partner_shipping_id.city or "",
            self.partner_shipping_id.state_id.display_name or "",
            self.partner_shipping_id.zip or "",
            self.partner_shipping_id.country_id.name or "",
            self.partner_shipping_id.phone or "",
            self.partner_shipping_id.email or "",
            self.name.lstrip("INV/"),
            format_date(self.env, self.invoice_date),
            self._get_customer_purchase_order_number(),
            self.ref or "",
            self.currency_id.name,
            "%.2f " % self.amount_total
        ]
        for line in self.invoice_line_ids.filtered(lambda x: not x.display_type).sorted(key=lambda l: (-l.sequence, l.date, l.move_name, -l.id), reverse=True):
            if line.display_type:
                line_values = [""] * len(header)
                line_values[0] = line.name or ""
            else:
                line_values = [
                    ",".join([sale_line.edi_order_line_number for sale_line in line.sale_line_ids if sale_line.edi_order_line_number]) or "",
                    line.product_id.default_code or "",
                    line.product_id.fisher_product_code or "",
                    line.name or "",
                    line.intrastat_product_origin_country_id.display_name or "",
                    int(line.quantity),
                    line.product_uom_id.display_name or "",
                    "%.2f" % line.price_unit,
                    "%.2f" % line.discount,
                    "%.2f" % line._edi_get_discount_value(),
                    "%.2f" % line._edi_get_discounted_price_before_tax(),
                    ",".join(line.tax_ids.mapped('name')),
                    "%.2f" % line._edi_get_sales_tax(),
                    line._edi_get_tax_percentage(),
                    "%.2f" % line._edi_get_taxed_price_without_discount(),
                    line.product_id.intrastat_id.code or "",
                    "%.2f" % line.price_total
                ]
                line_values = invoice_values + line_values
            values.append(line_values)

        return values

    def _get_customer_purchase_order_number(self):
        "fetch and return customer_purchase_order_number from the sale order"

        sale_order = self.env["sale.order"].sudo().search([("name", "=", self.invoice_origin)], limit=1)
        if sale_order:
            return sale_order.customer_purchase_order_number or ""
        else:
            return ""

class JournalItem(models.Model):
    _inherit = "account.move.line"

    def _edi_get_discount_value(self):
        "returns the discount value for the given invoice line"

        return (self.price_unit * self.quantity) - self.price_subtotal

    def _edi_get_discounted_price_before_tax(self):
        "returns the line total with discount before applying taxes"

        return self.price_subtotal

    def _edi_get_sales_tax(self):
        "returns tax amount of the invoice"

        # line_discount_price_unit = self.price_unit * (1 - (self.discount / 100.0))
        # taxes_res = self.tax_ids._origin.with_context(force_sign=1).compute_all(line_discount_price_unit,
        #         quantity=self.quantity, currency=self.currency_id, product=self.product_id, partner=self.partner_id, is_refund=self.move_id.move_type in ('out_refund', 'in_refund'))
        # _logger.info(f"\n==>taxes_res: {taxes_res}")
        return self.price_total - self.price_subtotal

    def _edi_get_tax_percentage(self):
        "returns the tax percentages applied on the invoice line"

        taxes = self.tax_ids.mapped(lambda tax: str(round(tax.amount, 2)))
        return ", ".join(taxes)

    def _edi_get_taxed_price_without_discount(self):
        "returns the total price including taxes without discount"

        prices = self._get_price_total_and_subtotal_model(
            price_unit = self.price_unit,
            quantity = self.quantity,
            discount = 0,
            currency = self.currency_id,
            product = self.product_id,
            partner = self.partner_id,
            taxes = self.tax_ids,
            move_type = self.move_id.move_type
        )
        return prices["price_total"]



