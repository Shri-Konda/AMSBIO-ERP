# -*-coding: utf-8 -*-

import os
import base64
import logging
import paramiko
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning
from odoo.modules.module import get_module_resource


_logger = logging.getLogger(__name__)

class FTPServer(models.Model):
    _name = "ftp.server"
    _description = "FTP Server"
    _inherit = ["mail.thread"]
    _order = "sequence"

    name = fields.Char(required=True)
    sequence = fields.Integer()
    active = fields.Boolean(default=True)

    hostname = fields.Char(required=True)
    import_username = fields.Char(required=True)
    import_password = fields.Char(required=True)

    export_username = fields.Char(required=True)
    export_password = fields.Char(required=True)
    state = fields.Selection(selection=[
        ("draft", "Not Connected"),
        ("connected", "Connected")
    ], default="draft")
    partner_id = fields.Many2one("res.partner", "Customer", check_company=True, required=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, required=True, help="Select the company for which orders, deliveries, and invoices will be exchanged through this FTP server.")

    def get_local_import_folder(self):
        return self.local_import_location

    @api.model
    def get_export_deliveries_folder(self):
        return get_module_resource("ti_amsbio_edi", "export_folder/export_deliveries")

    @api.model
    def get_export_invoices_folder(self):
        return get_module_resource("ti_amsbio_edi", "export_folder/export_invoices")

    @api.model
    def get_export_orders_folder(self):
        return get_module_resource("ti_amsbio_edi", "export_folder/export_orders")
    
    local_import_location = fields.Char(string="Local Import Location", required=True, help="Files will be stored temporarily in this directory before processing")
    ftp_import_location = fields.Char(string="FTP Source Location", required=True, help="FTP Location from to download order csv files.")
    ftp_order_location = fields.Char(string="Order Directory", required=True, help="Directory in FTP server where Order csvs will be uploaded.")
    ftp_delivery_location = fields.Char(string="Delivery Directory", required=True, help="Directory in FTP server where Delivery Order csvs will be uploaded.")
    ftp_invoice_location = fields.Char(string="Invoice Directory", required=True, help="Directory in FTP server where Invoice csvs will be uploaded.")

    failed_order_count = fields.Integer(string="Failed Orders", compute="_compute_order_count")
    order_count = fields.Integer(string="Orders", compute="_compute_order_count")
    delivery_count = fields.Integer(string="Deliveries", compute="_compute_order_count")
    invoice_count = fields.Integer(string="Invoices", compute="_compute_order_count")

    def _compute_order_count(self):
        for server in self:
            server.failed_order_count = self.env["ftp.server.log"].search_count([('ftp_server_id', '=', server.id), ('state', '=', "fail")])
            server.order_count = self.env["sale.order"].search_count([('ftp_server_id', '=', server.id)])
            server.delivery_count = self.env["stock.picking"].search_count([('ftp_server_id', '=', server.id), ('sent_to_edi', '=', True)])
            server.invoice_count = self.env["account.move"].search_count([('ftp_server_id', '=', server.id), ('sent_to_edi', '=', True)])

    _sql_constraints = [
        ('ftp_company_unique', 'unique (hostname,company_id)', 'FTP server must be unique for a company. You cannot have multiple servers with same hostname.'),
    ]

    def write(self, vals):
        "When hostname, username, and password are changed, then we have to make a test connection again so resetting it back"

        if "hostname" in vals or "import_username" in vals or "import_password" in vals or "export_username" in vals or "export_password" in vals:
            vals.update({'state': "draft"})
        return super(FTPServer, self).write(vals)

    def action_test_connection(self):
        "Check and connect to FTP server based on given credentials"

        self.ensure_one()
        # check connection with import credentials
        self._connect_to_ftp_server(self.hostname, self.import_username, self.import_password)
        self._connect_to_ftp_server(self.hostname, self.export_username, self.export_password)
        # If connection is successfull, set the state to connected
        if self.state == "draft":
            self.write({'state': "connected"})
        return {
            'type'  : "ir.actions.client",
            'tag'   : "display_notification",
            'params': {
                'title'  : _("Connected Successfully!"),
                'message': _("Everything seems properly setup!"),
                'sticky' : False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

    @api.model
    def _connect_to_ftp_server(self, hostname, username, password):
        "Connect to ftp server and return server handler"

        self.ensure_one()
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh_client.connect(hostname=hostname, username=username, password=password, look_for_keys=False)
        except Exception as e:
            msg = _("Error while connecting to %s with user %s: %s" % (hostname, username, e))
            raise UserError(msg)
        else:
            return ssh_client

    @api.model
    def _get_ftp_servers(self):
        "return all ftp servers which are connected"

        ftp_servers = self.sudo().search([('state', '=', "connected")])
        if ftp_servers:
            return ftp_servers
        else:
            action = self.env.ref("ti_amsbio_edi.action_ftp_server")
            msg = _("There are no active FTP servers. Please configure on to enable EDI integration.")
            raise RedirectWarning(msg, action.id, _("Configure FTP Server"))

    def send_files_to_ftp(self, upload_from, upload_to):
        """
        This method connects to FTP server and uploads files from local directory to remote.
        @param {str} upload_from: local directory from where files will be uploaded
        @param {str} upload_to: remote directory where files will be uploaded
        """

        self.ensure_one()
        if not upload_to:
            raise UserError(_("Please specify destination location on %s to upload files." % self.name))

        if not upload_from:
            raise UserError(_("Please specify source directory from where files will be uploaded."))

        ssh_client = self._connect_to_ftp_server(self.hostname, self.export_username, self.export_password)
        # _logger.info(f"\n==>ssh_client: {ssh_client} ==>upload_from: {upload_from} ==>upload_to: {upload_to}")
        try:
            # change current directory to upload_from
            os.chdir(upload_from)
            local_files = [file for file in os.listdir() if file.lower().endswith(".csv")]
            # _logger.info(f"\n==>local_files: {local_files}")
            if local_files:
                remote_loc = upload_to
                with ssh_client.open_sftp() as sftp_client:
                    # change directory to remote loc
                    sftp_client.chdir(remote_loc)
                    for file in local_files:
                        # _logger.info(f"\n==>{file}")
                        sftp_client.put(file, file, confirm=False)

                        msg = "Successfully sent following file to FTP server: <strong>%s</strong>" % file
                        self.message_post(body=_(msg))
                        # once file are uploaded to FTP server, delete them from local directory
                        os.remove(file)
            else:
                _logger.info(f"\n==>No new files found on [{self.name} - {upload_from}]")
        except Exception as e:
            msg = _("Error when uploading files to %s: %s" % (self.name, e))
            raise UserError(msg)

    def download_files_from_ftp(self, download_from, download_to):
        """
        This method downloads files from FTP server and stores them in local directory.
        @param {str} download_from: remote location from where files will be downloaded.
        @param {str} download_to: local directory where downloaded files will be stored.
        """

        self.ensure_one()
        if not download_from:
            raise UserError(_("Please specify source directory on %s to download files from." % self.name))

        if not download_to:
            raise UserError(_("Please specify destination directory where downloaded files will be store."))

        ssh_client = self._connect_to_ftp_server(self.hostname, self.import_username, self.import_password)
        try:
            remote_loc = download_from
            with ssh_client.open_sftp() as sftp_client:
                # change directory to remote loc
                sftp_client.chdir(remote_loc)
                ftp_files = [file for file in sftp_client.listdir() if file.lower().endswith(".csv")]
                if ftp_files:
                    for file in ftp_files:
                        local_file = os.path.join(download_to, file)
                        _logger.info(f"\n==>{file} ==> {local_file}")
                        sftp_client.get(file, local_file, prefetch=False)

                        msg = "Successfully downloaded following file from FTP server: <strong>%s</strong>" % file
                        self.message_post(body=_(msg))

                        # delete file from FTP server once file is downloaded successfully.
                        sftp_client.remove(file)
                else:
                    _logger.info(f"\n==>No new files found on [{self.name}-{remote_loc}]")
        except Exception as e:
            msg = _("Error when downloading files from %s: %s" % (self.name, e))
            raise UserError(msg)

    @api.model
    def create_file_attachment(self, file_path):
        "creates and returns attachment of the given file"

        data = open(file_path, "rb").read()
        filename = os.path.basename(file_path)
        attachment = self.env["ir.attachment"].sudo().create({
            'name'  : filename,
            'datas' : base64.b64encode(data),
            'type'  : "binary"
        })
        return attachment

    def action_open_failed_log(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id("ti_amsbio_edi.action_ftp_server_log")
        action["domain"] = [('ftp_server_id', '=', self.id), ('state', '=', "fail")]
        return action

    def action_open_orders(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('sale.act_res_partner_2_sale_order')
        action["domain"] = [("ftp_server_id", "=", self.id)]
        return action

    def action_open_deliveries(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        action["domain"] = [("ftp_server_id", "=", self.id), ('sent_to_edi', '=', True)]
        return action

    def action_open_invoices(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action["domain"] = [("ftp_server_id", "=", self.id), ('sent_to_edi', '=', True)]
        return action


class FTPServerLog(models.Model):
    _name = "ftp.server.log"
    _description = "FTP Server Log"

    ftp_server_id = fields.Many2one("ftp.server", string="FTP Server", required=True, ondelete="cascade")
    order_id = fields.Many2one("sale.order", ondelete="cascade")
    attachment_id = fields.Many2one("ir.attachment", string="CSV File")
    state = fields.Selection(selection=[("fail", "Failed"), ("done", "Done")])
    failure_reason = fields.Text(string="Failure Reason")

    def name_get(self):
        names = []
        for log in self:
            name = "%s - %s" % (log.ftp_server_id.name, log.attachment_id.name)
            names.append((log.id, name))
        return names

    def action_download_attachment(self):
        self.ensure_one()
        url = "%s/web/content/%s?download=true" % (self.attachment_id.get_base_url(), self.attachment_id.id)
        return {
            'type'  : "ir.actions.act_url",
            'target': "self",
            'url'   : url
        }

    def action_order_done(self):
        "Mark the log as done in case order was created manually."

        return {
                'name'     : _('Select Order'),
                'view_mode': 'form',
                'res_model': 'select.edi.order',
                'view_id'  : self.env.ref('ti_amsbio_edi.select_edi_order_view_form').id,
                'type'     : 'ir.actions.act_window',
                'target'   : 'new'
            }

    @api.autovacuum
    def _gc_ftp_server_log(self):
        "Perform garbage collection and unlink old completed logs"

        date = datetime.now()-timedelta(days=30)
        logs = self.sudo().search([('create_date', "<", date)])
        logs.unlink()
