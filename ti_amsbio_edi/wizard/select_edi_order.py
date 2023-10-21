# -*-coding: utf-8 -*-

import logging
from odoo import models, fields, _

_logger = logging.getLogger(__name__)

class SelectEDIOrder(models.TransientModel):
    _name = "select.edi.order"
    _description = "Select EDI Order"

    order_id = fields.Many2one("sale.order", required=True, string="Order", help="Select quotation/order created manually with the csv file of this log")

    def action_mark_done(self):
        "Update FTP server information on selected order and also update server log with order"

        log_id = self._context.get("active_id")
        log = self.env["ftp.server.log"].sudo().browse(log_id)

        # update sale order with FTP info
        self.order_id.write({'is_edi_order': True, 'ftp_server_id': log.ftp_server_id.id})
        self.order_id.message_post(body=_("Please find attached the csv file from EDI integration this order has been linked to."), attachment_ids=log.attachment_id.ids)

        # update log with order info
        log.write({'state': "done", "order_id": self.order_id.id})
