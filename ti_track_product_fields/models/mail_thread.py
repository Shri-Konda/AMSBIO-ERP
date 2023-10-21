# -*-coding: utf-8 -*-

import logging
from odoo import models, api, tools


_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'


    @tools.ormcache('self.env.uid', 'self.env.su')
    def _track_get_fields(self):
        """ override method to return product fields which should be tracked """

        if self._name =='product.template':
            remove_fields = ('write_date','message_unread','create_uid','__last_update','activity_exception_icon','activity_summary','create_date','activity_type_icon','message_is_follower','write_uid','message_follower_ids','message_unread_counter','activity_type_id','activity_state')
            # _logger.info(f"\n==>Fields: {self._fields}\n")
            fields = {
                name
                for name, field in self._fields.items()
                if name not in remove_fields
            }
            # _logger.info(f"\n==>Tracking fields: {fields}\n")
            return fields and set(self.fields_get(fields))
        else:
            return super(MailThread, self)._track_get_fields()
        