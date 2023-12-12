# -*- coding: utf-8 -*-

import logging

from odoo import api, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class mail_thread(models.AbstractModel):
    """
    Overwrite to redefine message routing and process corresponding exceptions
    """
    _inherit = "mail.thread"

    @api.model
    def message_route(self, message, message_dict, model=None, thread_id=None, custom_values=None):
        """
        Overwrite to catch and mark unattached messages

        1. Send notificaion if defined in settings
        """
        res = []
        try:
            res = super(mail_thread, self).message_route(
                message, message_dict, model=model,
                thread_id=thread_id, custom_values=custom_values
            )
        except ValueError:
            parent_object_id = self._get_lost_parent()
            message_dict.update({
                "is_unattached": True,
                "model": "lost.message.parent",
                "res_id": parent_object_id.id,
            })
            message_id = self._create_lost_message(**message_dict)
            _logger.warning(u"Message {} can't be routed. Assign it to 'lost messages'".format(message_id))
            # 1
            Config = self.env["ir.config_parameter"].sudo()
            notify_about_lost_messages = safe_eval(Config.get_param("notify_about_lost_messages", "False"))
            if notify_about_lost_messages:
                notify_lost_user_ids =  safe_eval(Config.get_param("notify_lost_user_ids", "[]"))
                if notify_lost_user_ids:
                    try:
                        self = self.sudo()
                        user_ids = self.env["res.users"].search([("id", "in", notify_lost_user_ids)])
                        partner_ids = user_ids.mapped("partner_id")
                        context = self.env.context.copy()
                        action = self.env.ref("mail_manual_routing.mail_message_action_unattached_open_only_form").id
                        base_url = Config.get_param("web.base.url")
                        db = self.env.cr.dbname
                        url = "{}/web?db={}#id={}&action={}".format(base_url, db, message_id.id, action)
                        context.update({"url": url})
                        template = self.env.ref("mail_manual_routing.lost_message_notification_template")
                        body_html = template.with_context(context)._render_template_qweb(
                            template.body_html, "mail.message", [message_id.id], add_context=context,
                        ).get(message_id.id)
                        subject = template.with_context(context)._render_template_inline_template(
                            template.subject, "mail.message", [message_id.id], add_context=context,
                        ).get(message_id.id)
                        parent_object_id.message_post(body=body_html, subject=subject, partner_ids=partner_ids.ids)
                    except Exception as e:
                        _logger.error("Notification by lost message {} is not sent. Reason: {}".format(message_id, e))
        return res

    @api.returns("mail.message", lambda value: value.id)
    def _create_lost_message(
        self, *, body="", subject=None, message_type="notification", email_from=None, author_id=None, parent_id=False,
        subtype_xmlid=None, subtype_id=False, partner_ids=None, attachments=None, attachment_ids=None, **kwargs):
        """
        The method to prepare lost message and create it.
        It represents a modified copy of message_post 
        """
        msg_kwargs = dict((key, val) for key, val in kwargs.items() if key in self.env["mail.message"]._fields)
        notif_kwargs = dict((key, val) for key, val in kwargs.items() if key not in msg_kwargs)

        partner_ids = set(partner_ids or [])
        self = self._fallback_lang()
        if self.env.user._is_public() and "guest" in self.env.context:
            author_guest_id = self.env.context["guest"].id
            author_id, email_from = False, False
        else:
            author_guest_id = False
            author_id, email_from = self._message_compute_author(author_id, email_from, raise_on_email=True)
        
        if subtype_xmlid:
            subtype_id = self.env["ir.model.data"]._xmlid_to_res_id(subtype_xmlid)
        if not subtype_id:
            subtype_id = self.env["ir.model.data"]._xmlid_to_res_id("mail_mt_note")

        msg_values = dict(msg_kwargs)
        if "email_add_signature" not in msg_values:
            msg_values["email_add_signature"] = True
        
        msg_values.update({
            "author_id": author_id,
            "author_guest_id": author_guest_id,
            "email_from": email_from,
            "body": body,
            "subject": subject or False,
            "message_type": message_type,
            "subtype_id": subtype_id,
            "partner_ids": partner_ids,
        })

        attachments = attachments or []
        attachment_ids = attachment_ids or []
        attachement_values = self._message_post_process_attachments(attachments, attachment_ids, msg_values)
        msg_values.update(attachement_values) 
        message_id = self._message_create(msg_values)
        return message_id

    @api.model
    def _get_lost_parent(self):
        """
        The method to find or create a parent object which would server to overcome super rights

        Returns:
         * lost.message.parent object
        """
        self = self.sudo()
        lost_parent_id = self.env["lost.message.parent"].search([], limit=1)
        if not lost_parent_id:
            lost_parent_id = self.env["lost.message.parent"].with_context(mail_create_nosubscribe=True).create({})
        return lost_parent_id
