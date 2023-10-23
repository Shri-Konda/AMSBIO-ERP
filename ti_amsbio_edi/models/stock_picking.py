# -*-coding: utf-8 -*-

import csv
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    sent_to_edi = fields.Boolean(default=False, string="Sent To EDI", readonly=True, copy=False)
    ftp_server_id = fields.Many2one("ftp.server", string="EDI FTP Server", readonly=True, help="Stores FTP server record if transfer is created for order which was created from EDI.")

    @api.model
    def cron_edi_export_delivery_orders(self):
        "Prepare and send csv files for delivery orders for orders created through EDI"

        ftp_servers = self.env["ftp.server"]._get_ftp_servers()
        _logger.info(f"\n==>ftp_servers: {ftp_servers}")
        for server in ftp_servers:
            domain = [
                ('ftp_server_id', '=', server.id),
                ('sent_to_edi', '=', False),
                ('state', '=', "done")
            ]
            deliveries_to_send = self.sudo().search(domain)
            _logger.info(f"\n==>deliveries for {server.name}: {deliveries_to_send.mapped('name')}")
            delivery_export_folder = server.get_export_deliveries_folder()
            for delivery in deliveries_to_send:
                try:
                    delivery._create_edi_delivery_csv(delivery_export_folder)
                    delivery.write({'sent_to_edi': True})
                except Exception as e:
                    msg = "Error while creating EDI csv: <strong>%s</strong>" % e
                    delivery.message_post(body=_(msg))

            # onces files are created, send csv files to FTP server
            upload_to = server.ftp_delivery_location
            server.send_files_to_ftp(delivery_export_folder, upload_to)

    def _create_edi_delivery_csv(self, delivery_export_folder):
        "Prepare a csv file for the delivery order which will be sent FTP server"

        self.ensure_one()
        delivery_values = self._prepare_edi_delivery_values()
        if delivery_values:
            filepath = f"{delivery_export_folder}/ASN_{self.name.replace('/', '_')}.csv"
            with open(filepath, "w") as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerows(delivery_values)

            # create attachment and post message on delivery
            attachment = self.env["ftp.server"].create_file_attachment(filepath)
            attachment.write({'res_model': "stock.picking", 'res_id': self.id})
            msg = "Successfully created delivery order csv file for EDI. Please find attached the csv file."
            _logger.info(f"\n==>msg: {msg}")
            self.message_post(body=_(msg), attachment_ids=attachment.ids)

    def _prepare_edi_delivery_values(self):
        "Prepare values for EDI csv"

        self.ensure_one()
        header = [
            "Date",
            "Customer Account Number",
            "Delivery Address Street",
            "Delivery Address Street2",
            "Delivery Address City",
            "Delivery Address State",
            "Delivery Address Zip",
            "Delivery Address Country",
            "Delivery Address Phone",
            "Delivery Address Email",
            "Order No",
            "Delivery Note",
            "Customer Purchase Order Number",
            "Courier Reference",
            "Carrier Name",
            "Carrier Code",
            "Your Reference",
            "Order Line Number",
            "Code",
            "Description",
            "Packsize",
            "Storage Condition",
            "Shipping Temperature",
            "Tariff Code",
            "Quantity",
            "UoM"
        ]

        values = [header]
        intercompany_sale_order = self.env["sale.order"].sudo().search([("name", "=", self.intercompany_sale_order)], limit=1)
        delivery_values = [
            self.date_done.strftime("%d/%m/%Y") if self.date_done else "",
            self.partner_id.amsbio_edi_account_number or "",
            self.partner_id.street or "",
            self.partner_id.street2 or "",
            self.partner_id.city or "",
            self.partner_id.state_id.display_name or "",
            self.partner_id.zip or "",
            self.partner_id.country_id.name or "",
            self.partner_id.phone or "",
            self.partner_id.email or "",
            self.intercompany_sale_order or "",
            self.name,
            intercompany_sale_order and intercompany_sale_order.customer_purchase_order_number or "",
            intercompany_sale_order and intercompany_sale_order.x_studio_courier_ref or "",
            "FedEx",
            "FDEN",
            intercompany_sale_order and intercompany_sale_order.client_order_ref or "",
        ]
        for move in self.move_ids.filtered(lambda move: move.sale_line_id.edi_order_line_number):
            line_valuse = [
                move.sale_line_id.edi_order_line_number,
                move.product_id.default_code or "",
                move.name or "",
                1,
                move.product_id.x_studio_storage_temperature or "",
                move.product_id.x_studio_shipping_temperature or "",
                move.product_id.intrastat_code_id.code or "",
                int(move.product_uom_qty),
                move.product_uom.display_name or ""
            ]
            values.append(delivery_values + line_valuse)
        return values


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_new_picking_values(self):
        "When creating delivery, if sale order is created from EDI then pass FTP server record to delivery order as well"

        vals = super(StockMove, self)._get_new_picking_values()
        # Get the note from the sale order
        order = self.mapped("sale_line_id.order_id")[0]
        if order:
            intercompany_sale_order = self.env["sale.order"].sudo().search([("name", "=", order.intercompany_sale_order)], limit=1)
            # _logger.info(f"\n==>order: {order.name} ==>intercompany_sale_order: {intercompany_sale_order.name}")
            if intercompany_sale_order and intercompany_sale_order.ftp_server_id:
                vals["ftp_server_id"] = intercompany_sale_order.ftp_server_id.id
        # _logger.info(f"\n==>self: {self} ==>vals: {vals}")
        return vals