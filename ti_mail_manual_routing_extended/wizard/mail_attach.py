# -*-coding: utf-8 -*-

import logging
from odoo import models

_logger = logging.getLogger(__name__)

class MailAttachWizard(models.TransientModel):
    _inherit = "mail.message.attach.wizard"

    def action_attach_mail_message(self):
        "override method to update previous converstation field on lead/contact/sale order"

        result = super(MailAttachWizard, self).action_attach_mail_message()
        # _logger.info(f"\n==>res_reference: {self.res_reference._name}")
        if self.res_reference._name in ["crm.lead", "res.partner", "sale.order"]:
            record = self.env[self.res_reference._name].browse(self.res_reference.id)
            # _logger.info(f"\n==>record: {record}")
            record.write({'amsbio_previous_conversation': "\n".join(self.message_ids.mapped('body'))})

        return result