# -*-coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import models, api, fields, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _cron_execute_followup(self):
        "override method to pass in context that followup is done through cron"


        for company in self.env["res.company"].search([]):
            # Since the cache is done by database and not by company, we need to invalidate in this special case
            # where the context is changing in the same transaction
            self.env.cr.execute("DROP TABLE IF EXISTS followup_data_cache")
            self.with_context(allowed_company_ids=company.ids, followup_from_cron=True)._cron_execute_followup_company()

    def _get_followup_responsible(self):
        "override method to return responsible user"

        self.ensure_one()
        if self._context.get("followup_from_cron", False):
            return super(ResPartner, self)._get_followup_responsible()
        else:
            return self.env.user

class CrmLead(models.Model):
    _inherit = "crm.lead"

    is_salesperson_notified = fields.Boolean(default=False, help="True if salesperson is notified for unattained opporutnity")

    @api.model
    def _cron_notify_for_unattained_opportunities(self):
        """notify and create activity for salesperson if opportunity is not moved ahead for a week"""

        unattained_opportunities = self.search([("stage_id.name", '=', "Qualified"), ('date_last_stage_update', '<=', fields.Datetime.today()-relativedelta(days=7)), ('is_salesperson_notified', '=', False)])
        crm_model = self.env["ir.model"].search([('model', '=', 'crm.lead')], limit=1)
        for opporutnity in unattained_opportunities.filtered("user_id"):
            try:
                todo_vals = {
                    'res_id': opporutnity.id,
                    'res_model_id': crm_model.id,
                    'activity_type_id': self.env.ref("mail.mail_activity_data_todo").id,
                    'user_id': opporutnity.user_id.id,
                    'summary': "Opportunity Follow-up",
                    'note': "This opportunity has not been moved to next stage for a week. Please review and update.",
                    'date_deadline': fields.Date.today()
                }
                self.env["mail.activity"].create(todo_vals)
                opporutnity.write({'is_salesperson_notified': True})
            except Exception as e:
                msg = f"There was an error when scheduling activity for salesperson: {e}"
                opporutnity.message_post(body=_(msg))

class SaleOrder(models.Model):
    _inherit = "sale.order"

    first_quote_reminder_date = fields.Datetime(string="First Reminder Date", readonly=True, help="Date first notification sent to customer or salesperson if quote not confirmed after a week of creation")
    second_quote_reminder_date = fields.Datetime(string="Second Reminder Date", readonly=True, help="Date second notification sent to customer or salesperson if quote not confirmed after a 2 weeks of first reminder")
    unfullfilled_notification_sent = fields.Boolean(default=False, string="Notified Salesperson for Unfullfilled Order?")

    @api.model
    def _cron_notify_for_outstanding_quotations(self):
        """notify customer or salesperson for quotes which are not confirmed after 1-3 weeks of creation"""

        first_reminder_quotes = self.search([("state", 'in', ["draft", "sent"]), ('create_date', '<=', fields.Datetime.today()-relativedelta(days=7)), ('first_quote_reminder_date', '=', False)])
        sale_order_model = self.env["ir.model"].search([('model', '=', 'sale.order')], limit=1)
        for quote in first_reminder_quotes:
            try:
                if quote.amount_total <= 1000:
                    template = self.env.ref("ti_amsbio_crm_notification.amsbio_crm_quote_first_reminder_template")
                    if template:
                        template.send_mail(quote.id, force_send=True)
                elif quote.user_id:
                    todo_vals = {
                    'res_id': quote.id,
                    'res_model_id': sale_order_model.id,
                    'activity_type_id': self.env.ref("mail.mail_activity_data_todo").id,
                    'user_id': quote.user_id.id,
                    'summary': "Quotation pending for a week",
                    'note': "This quotation has not been confirmed after a week of creation. Please review and update.",
                    'date_deadline': fields.Date.today()
                }
                    self.env["mail.activity"].create(todo_vals)
                quote.write({'first_quote_reminder_date': fields.Datetime.now()})
            except Exception as e:
                msg = f"There was an error sending first reminder notification: {e}"
                quote.message_post(body=_(msg))

        second_reminder_quotes =  self.search([("state", 'in', ["draft", "sent"]), ('first_quote_reminder_date', '<=', fields.Datetime.today()-relativedelta(days=14)), ('second_quote_reminder_date', '=', False)])
        for quote in second_reminder_quotes:
            try:
                if quote.amount_total <= 1000:
                    template = self.env.ref("ti_amsbio_crm_notification.amsbio_crm_quote_second_reminder_template")
                    if template:
                        template.send_mail(quote.id, force_send=True)
                elif quote.user_id:
                    todo_vals = {
                    'res_id': quote.id,
                    'res_model_id': sale_order_model.id,
                    'activity_type_id': self.env.ref("mail.mail_activity_data_todo").id,
                    'user_id': quote.user_id.id,
                    'summary': "Quotation pending for a 3 weeks",
                    'note': "This quotation has not been confirmed after 3 weeks of creation. Please review and updates.",
                    'date_deadline': fields.Date.today()
                }
                self.env["mail.activity"].create(todo_vals)
                quote.write({'second_quote_reminder_date': fields.Datetime.now()})
            except Exception as e:
                msg = f"There was an error sending seccond reminder notification: {e}"
                quote.message_post(body=_(msg))

    @api.model
    def _cron_notify_for_unfullfilled_orders(self):
        """notify salesperson for sale orders which are not delivered within week after ordered"""

        unfullfilled_orders = self.search([("state", "=", "sale"), ('date_order', '<=', fields.Datetime.today()-relativedelta(days=7)), ('delivery_status', '=', "pending"), ('unfullfilled_notification_sent', '=', False)])
        sale_order_model = self.env["ir.model"].search([('model', '=', 'sale.order')], limit=1)
        for order in unfullfilled_orders.filtered("user_id"):
            try:
                todo_vals = {
                    'res_id': order.id,
                    'res_model_id': sale_order_model.id,
                    'activity_type_id': self.env.ref("mail.mail_activity_data_todo").id,
                    'user_id': order.user_id.id,
                    'summary': "Order Not Delivered",
                    'note': "Order has not been deliverd after a week of order. Please review and add reason on chatter.",
                    'date_deadline': fields.Date.today()
                }
                self.env["mail.activity"].create(todo_vals)
                order.write({'unfullfilled_notification_sent': True})
            except Exception as e:
                msg = f"There was an error when scheduling activity for salesperson: {e}"
                order.message_post(body=_(msg))

