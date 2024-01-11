# -*-coding: utf-8 -*-

import re
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, api


_logger = logging.getLogger(__name__)

class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.returns("mail.message", lambda value: value.id)
    def _create_lost_message(
        self, *, body="", subject=None, message_type="notification", email_from=None, author_id=None, parent_id=False,
        subtype_xmlid=None, subtype_id=False, partner_ids=None, attachments=None, attachment_ids=None, **kwargs):
        """override this method to automatically assign lost message to a contact"""

        message_id = super(MailThread, self)._create_lost_message(body=body, subject=subject, message_type=message_type, email_from=email_from, author_id=author_id, \
                                                                  parent_id=parent_id, subtype_xmlid=subtype_xmlid, subtype_id=subtype_id, partner_ids=partner_ids,\
                                                                    attachments=attachments, attachment_ids=attachment_ids, **kwargs)
        if message_id and message_id.body:
            try:
                # find the last email from from the email thread
                from_pattern = r'From:(.+?)>'
                from_addresses = re.findall(from_pattern, message_id.body.striptags())
                if from_addresses:
                    from_address = from_addresses[0]
                    name, email = from_address.split("<")

                    # search for existing contact with given email address
                    if email:
                        contact = self.env["res.partner"].sudo().search([("email", "=", email.strip())], limit=1)
                        # _logger.info(f"\n==>email: {email} ==>contact: {contact}")
                        if contact:
                            new_message = ""
                            if message_id.body:
                                new_message += message_id.body + "\n"
                            if contact.amsbio_previous_conversation:
                                new_message += contact.amsbio_previous_conversation
                            contact.write({'amsbio_previous_conversation': new_message})
                        else:
                            # create new contact with given email address
                            contact = self.env["res.partner"].sudo().create({'name': name, 'email': email})
                            contact.write({'amsbio_previous_conversation': message_id.body})
                            # _logger.info(f"\n==>contact created: {contact}")
            except Exception as e:
                _logger.warning(f"\n==>There was an error during automatic routing of message: {message_id.id}")

        return message_id
    
class mail_message(models.Model):
    _inherit = "mail.message"

    @api.model
    def _cron_clean_old_lost_messages(self):
        """delete lost messages which are not routed"""

        lost_messages = self.search([('is_unattached', '=', True), ('model', '=', "lost.message.parent"), ('create_date', '<=', datetime.today()-relativedelta(days=7))])
        # _logger.info(f"\n==>deleting old messages: {lost_messages}")
        lost_messages.unlink()