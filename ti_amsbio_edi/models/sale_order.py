# encoding: utf-8 -*-

import os
import csv
import logging
from psycopg2 import IntegrityError, InternalError
from odoo.tools import format_date
from odoo import models, fields, api, _, Command

_logger = logging.getLogger(__name__)

ORDER_FIELDS_TO_CHECK = ["target_delivery_date"]

class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_edi_order = fields.Boolean(string="EDI Order", default=False, readonly=True, copy=False, help="True is order is created from EDI Integration")
    ftp_server_id = fields.Many2one("ftp.server", string="FTP Server", check_company=True, readonly=True, copy=False,)
    customer_purchase_order_number = fields.Char(help="Purchase order number of the end customer")

    def write(self, vals):
        "override method to create order csv when certain values are updated"

        result = super(SaleOrder, self).write(vals)
        create_csv = False
        for field in ORDER_FIELDS_TO_CHECK:
            if field in vals:
                create_csv = True
                break
        # _logger.info(f"\n==>orders: {self.mapped('name')} ==>vals: {vals} ==>create_csv: {create_csv} ==>EDI order: {self.filtered('is_edi_order').mapped('name')}")
        if create_csv:
            for order in self.filtered(lambda sale: sale.is_edi_order and sale.state in ["sale"]):
                order.prepare_order_confirmation_csv()
        return result

    @api.model
    def cron_edi_import_orders(self):
        "Cron to import and create orders from FTP server"

        ftp_servers = self.env["ftp.server"]._get_ftp_servers()
        for server in ftp_servers:
            # download order files from FTP server
            import_from = server.ftp_import_location
            import_to = server.get_local_import_folder()
            server.download_files_from_ftp(import_from, import_to)

            # create orders in Odoo from downloaded files
            self.with_company(server.company_id)._create_edi_orders(server)

    @api.model
    def cron_edi_export_sale_orders(self):
        "Cron to send sale order csv files to FTP server"

        ftp_servers = self.env["ftp.server"]._get_ftp_servers()
        for server in ftp_servers:
            # upload order files to ftp server
            upload_from = server.local_export_order_location
            upload_to = server.ftp_order_location
            server.send_files_to_ftp(upload_from, upload_to)

    @api.model
    def _create_edi_orders(self, ftp_server):
        "Traverse over the order files and create sale order from them."

        import_folder = ftp_server.get_local_import_folder()
        os.chdir(import_folder)
        files = [file for file in os.listdir() if not file.startswith(".")]
        _logger.info(f"\n==>import_folder: {import_folder}\n==>files: {files}")
        for file in files:
            ftp_server_log_values = {}
            attachment = ftp_server.create_file_attachment(file)
            try:
                with self.env.cr.savepoint():
                    customer = ftp_server.partner_id
                    order_values = self._prepare_edi_order_values(customer, file)
                    order_values.update({
                        'partner_id'        : customer.id,
                        'partner_invoice_id': customer.address_get(["invoice"]).get("invoice"),
                        'is_edi_order'      : True,
                        'ftp_server_id'     : ftp_server.id
                    })
                    _logger.info(f"\n==>order_values: {order_values}")
                    order = self.create(order_values)
                    if order:
                        msg = "Order successfully created from EDI. Please find attached the csv file for more information"
                        # updating res_model and res_id on attachment
                        attachment.write({'res_model': "sale.order", 'res_id': order.id})
                        order.message_post(body=_(msg), attachment_ids=attachment.ids)

                        # add delivery address to main customer's contact as delivery address
                        if order.partner_shipping_id not in order.partner_id.child_ids:
                            order.partner_shipping_id.write({'parent_id': order.partner_id.id})

                        # create FTP Server log
                        ftp_server_log_values.update({
                            'ftp_server_id': ftp_server.id,
                            'order_id'     : order.id,
                            'attachment_id': attachment.id,
                            'state'         : "done"
                        })
            except (InternalError, IntegrityError) as e:
                msg = "Database error while creating order from EDI: %s <br/>Please find attached the csv file for more information." % e
                _logger.error(f"\n==>{msg}")
                attachment.write({'res_model': "ftp.server", 'res_id': ftp_server.id})
                ftp_server.message_post(body=_(msg), attachment_ids=attachment.ids)

                # create FTP Server log
                ftp_server_log_values.update({
                    'ftp_server_id': ftp_server.id,
                    'attachment_id': attachment.id,
                    'state'         : "fail",
                    'failure_reason': e
                })
            except Exception as e:
                msg = "Error while creating order from EDI: %s <br/>Please find attached the csv file for more information." % e
                _logger.error(f"\n==>{msg}")
                attachment.write({'res_model': "ftp.server", 'res_id': ftp_server.id})
                ftp_server.message_post(body=_(msg), attachment_ids=attachment.ids)

                 # values for server log
                ftp_server_log_values.update({
                    'ftp_server_id': ftp_server.id,
                    'attachment_id': attachment.id,
                    'state'         : "fail",
                    'failure_reason': e
                })
            finally:
                #  delete csv file from local directory since it's already attached on Odoo document
                os.remove(file)
                log = self.env["ftp.server.log"].sudo().create(ftp_server_log_values)

    def _prepare_edi_order_values(self, customer, file):
        "Parse the csv file and prepare order values to create sale order"

        order_values = {}
        order_line_values = []
        order_notes = []
        with open(file) as csv_file:
            csv_reader = csv.reader(csv_file)
            order_data = next(csv_reader)
            order_values.update(self._prepare_order_values(order_data))

            # Adding first line of data as well
            order_line_values.append(Command.create(self._prepare_order_line_values(customer, order_data)))
            if order_data[17]:
                order_notes.append(order_data[17])
            # Now preparing order line values
            for line_data in csv_reader:
                order_line_values.append(Command.create(self._prepare_order_line_values(customer, line_data)))
                if line_data[17]:
                    order_notes.append(line_data[17])

        # Add shipping costs and handling fees
        order_line_with_shipping = self._add_shipping_handling_costs(order_line_values)
        if order_notes:
            # adding a note in the order line
            order_line_with_shipping.append(Command.create({
                'name': ",".join(order_notes),
                'display_type': "line_note"
            }))

        order_values.update({
            'order_line': order_line_with_shipping
        })
        return order_values

    def _prepare_order_values(self, order_data):
        "Prepare customer information and order values from the given data"

        # TODO: mapping of fields once the sample csv is received from Trucommerce

        values = {}
        # check if customer exists for the given account number, if not then create customer
        customer = self._search_or_create_customer(order_data)
        values["partner_shipping_id"] = customer.id
        values.update({
            'client_order_ref': order_data[13],
            'customer_purchase_order_number': order_data[14]
        })
        return values

    def _search_or_create_customer(self, order_data):
        "look for customer with address and if not available, create new customer"

        # _logger.info(f"\n==>current_company: {self.env.company.name}")
        country_id = self.env.company.country_id.id
        name = order_data[4] and order_data[4].strip() or ""
        street = order_data[5] and order_data[5] or ""
        street2 = order_data[6] and order_data[6] or ""
        city = order_data[7] and order_data[7] or ""
        if order_data[8]:
            state_id = self.env["res.country.state"].sudo().search([("code", "=", order_data[8]), ('country_id', '=', country_id)], limit=1).id
        else:
            state_id = False
        zip = order_data[9] and order_data[9] or ""

        # search for customer
        customer = self.env["res.partner"].search([
            ('name', '=', name),
            ('street', '=', street),
            ('street2', '=', street2),
            ('city', '=', city),
            ('state_id', '=', state_id),
            ('country_id', '=', country_id),
            ('zip', '=', zip),
        ], limit=1)
        # _logger.info(f"\n==>address_domain: {address_domain} ==>customer: {customer}")
        if not customer:
            customer_values = {
                'name'      : name,
                'phone'     : order_data[11],
                'email'     : order_data[12],
                'street'    : street,
                'street2'   : street2,
                'city'      : city,
                'state_id'  : state_id,
                'country_id': country_id,
                'zip'       : zip,
                'type'      : "delivery",
                'amsbio_edi_account_number': order_data[2],
            }
            customer = self.env["res.partner"].create(customer_values)
        return customer


    def _prepare_order_line_values(self, customer, line_data):
        "Prepare order line values from the given data"

        values = {}
        product_code = str(line_data[15])
        product = self.env["product.product"].search([('default_code', "=", product_code)], limit=1)
        if product:
            price, discount = self._get_discount_from_edi_unit_price(customer, product, float(line_data[18]), float(line_data[19]))
            values.update({
            'product_id'     : product.id,
            'name'           : line_data[16] or product.description_sale,
            'product_uom_qty': line_data[18],
            'price_unit'     : price,
            'discount'       : discount,
        })
        else:
            product = self.env.ref("ti_amsbio_edi.amsbio_edi_missing_product")
            values.update({
                'product_id'     : product.id,
                'name'           : line_data[16] or product.description_sale,
                'product_uom_qty': line_data[18],
                'price_unit'     : line_data[19],
            })
        values.update({'edi_order_line_number': line_data[0]})
        return values

    @api.model
    def _get_discount_from_edi_unit_price(self, customer, product, qty, discounted_price):
        "calculates the discount from the unit price received from EDI and product price on Odoo"

        rule_id = customer.property_product_pricelist._get_product_rule(
                    product,
                    qty,
                    product.uom_id,
                    date=fields.Datetime.now(),
                )
        
        pricelist_rule = self.env['product.pricelist.item'].browse(rule_id)
        real_price = pricelist_rule._compute_price(
            product, qty, product.uom_id, fields.Datetime.now(), currency=customer.currency_id)
        
        if real_price:
            discount = ((real_price - discounted_price) / real_price) * 100
            return real_price, discount
        else:
            return discounted_price, 0.0



    def _add_shipping_handling_costs(self, order_line_values):
        "Add shipping costs and handling fees based on shipping temperature of products in order line"

        dry_ice_product = False
        ambient_gel_product = False
        for line in order_line_values:
            product = self.env["product.product"].browse(line[-1].get("product_id", None))
            if product:
                if product.x_studio_shipping_temperature == "Dry Ice":
                    # If order line has product which needs to be shipped in Dry Ice then all other products can be shipped as well,
                    # so we only need to add shipping and handling costs for Dry Ice
                    dry_ice_product = True
                    break
                elif product.x_studio_shipping_temperature == "Ambient/Gel Packs":
                    ambient_gel_product = True

        shipping_cost = self.env["product.product"]
        handling_fee = self.env["product.product"]
        if dry_ice_product:
            shipping_cost = self.env["product.product"].search([('fisher_product_code', "=", "C510")], limit=1)
        elif ambient_gel_product:
            shipping_cost = self.env["product.product"].search([("fisher_product_code", "=", "D240")], limit=1)
            handling_fee = self.env["product.product"].search([("fisher_product_code", "=", "D500")], limit=1)

        if shipping_cost:
            order_line_values.append(Command.create({'product_id': shipping_cost.id, 'product_uom_qty': 1}))
        if handling_fee:
            order_line_values.append(Command.create({'product_id': handling_fee.id, 'product_uom_qty': 1}))

        return order_line_values

    def action_confirm(self):
        "When order is confirmed and is EDI order, then send confirmation to FTP server"

        result = super(SaleOrder, self).action_confirm()
        for order in self.filtered("is_edi_order"):
            try:
                order.prepare_order_confirmation_csv()
            except Exception as e:
                msg = "Error while creating order confirmation csv file: %s" % e
                order.message_post(body=_(msg))
        return result

    def prepare_order_confirmation_csv(self):
        "Prepare a csv file which includes order confirmation details"

        order_export_folder = self.ftp_server_id.get_export_orders_folder()
        order_values = self._prepare_order_confirmation_csv_values()
        if order_values:
            filepath = f"{order_export_folder}/ACK_{self.name.replace('/', '_')}.csv"
            with open(filepath, "w") as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerows(order_values)

            # create attachment and post message on order
            attachment = self.ftp_server_id.create_file_attachment(filepath)
            attachment.write({'res_model': "sale.order", 'res_id': self.id})
            msg = "Successfully created order confirmation csv file for EDI. Please find attached the csv."
            _logger.info(f"\n==>msg: {msg}")
            self.message_post(body=(msg), attachment_ids=attachment.ids)

    def _prepare_order_confirmation_csv_values(self):
        "Prepare values for creating csv when order is confirmed"

        header = [
            "Order Reference",
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
            "Order Date",
            "Delivery Time",
            "Target Delivery Date",
            "Payment Terms",
            "Customer Purchase Order Number",
            "Customer Reference",
            "Currency",
            "Order Total",
            "Note",
            "Order Line Number",
            "Code No.",
            "Description",
            "Pack Size",
            "Quantity",
            "UoM",
            "Unit Price",
            "VAT",
            "Discount",
            "Total Price"
        ]

        values = [header]
        order_data = [
            self.name,
            self.partner_shipping_id.amsbio_edi_account_number or "",
            self.partner_invoice_id.street or "",
            self.partner_invoice_id.street2 or "",
            self.partner_invoice_id.city or "",
            self.partner_invoice_id.state_id.display_name or "",
            self.partner_invoice_id.zip or "",
            self.partner_invoice_id.country_id.name or "",
            self.partner_invoice_id.phone or "",
            self.partner_invoice_id.email or "",
            self.partner_shipping_id.street or "",
            self.partner_shipping_id.street2 or "",
            self.partner_shipping_id.city or "",
            self.partner_shipping_id.state_id.display_name or "",
            self.partner_shipping_id.zip or "",
            self.partner_shipping_id.country_id.name or "",
            self.partner_shipping_id.phone or "",
            self.partner_shipping_id.email or "",
            format_date(self.env, self.date_order),
            "%s week(s)" % self.delivery_time_week if self.delivery_time_week else "",
            self.target_delivery_date.strftime("%d/%m/%Y") if self.target_delivery_date else "",
            self.payment_term_id and self.payment_term_id.name or "",
            self.customer_purchase_order_number or "",
            self.client_order_ref or "",
            self.currency_id.name,
            "%.2f" % self.amount_total,
            self.note
        ]
        for line in self.order_line.filtered("edi_order_line_number"):
            if line.display_type:
                line_values = [""] * len(header)
                line_values[0] = line.name
            else:
                line_values = [
                    line.edi_order_line_number,
                    line.product_id.default_code or "",
                    line.name or "",
                    1,
                    int(line.product_uom_qty),
                    line.product_uom.display_name or "",
                    "%.2f" % line.price_unit,
                    "%.2f" % line.tax_id.amount or 0.0,
                    "%.2f" % line.discount,
                    "%.2f" % line.price_subtotal
                ]
                line_values = order_data + line_values
            values.append(line_values)
        return values

    def _prepare_invoice(self):
        "If sale order was created from EDI integration, then pass edi info to invoice as well"

        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if self.ftp_server_id:
            invoice_vals.update({'ftp_server_id': self.ftp_server_id.id})

        return invoice_vals


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    edi_order_line_number = fields.Char(string="EDI Order Line Number", readonly=True, copy=False, help="This order line number represents the order line number received from EDI integration.")

class ProductTemplate(models.Model):
    _inherit = "product.template"

    # These are the studio fields which we will be using in this integration, so we are redefining them to support workflow of this module
    x_studio_shipping_temperature = fields.Selection([
        ('Dry Ice', "Dry Ice"),
        ('Ambient/Gel Packs', "Ambient/Gel Packs")
    ], string="Shipping Temperature")
    x_studio_storage_temperature = fields.Char(string="Storage Conditions")

    fisher_product_code = fields.Char(string="Fisher Code")


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.model
    def _prepare_sale_order_line_data(self, line, company):
        "override method to pass EDI line number in intercompany sale order"

        values = super(PurchaseOrder, self)._prepare_sale_order_line_data(line, company)
        if line.sale_line_id.edi_order_line_number:
            values['edi_order_line_number'] = line.sale_line_id.edi_order_line_number

        _logger.info(f"\n==>intercompany sale order line values: {values}")
        return values

