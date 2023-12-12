# -*- coding: utf-8 -*-

from odoo import api, fields, models 
from odoo.tools.safe_eval import safe_eval


class res_config_settings(models.TransientModel):
    """
    Overwrite to add mail routing settings
    """
    _inherit = "res.config.settings"

    @api.depends("notify_lost_user_ids_str")
    def _compute_notify_lost_user_ids(self):
        """ 
        Compute method for notify_lost_user_ids 
        """
        for setting in self:
            notify_lost_user_ids = []
            if setting.notify_lost_user_ids_str:
                try:
                    notify_lost_users_list = safe_eval(setting.notify_lost_user_ids_str)
                    notify_lost_user_ids = self.env["res.users"].search([("id", "in", notify_lost_users_list)]).ids
                except:
                    notify_lost_user_ids = []
            setting.notify_lost_user_ids = [(6, 0, notify_lost_user_ids)]

    def _inverse_notify_lost_user_ids(self):
        """
        Inverse method for notify_lost_user_ids
        """
        for setting in self:
            notify_lost_user_ids_str = ""
            if setting.notify_lost_user_ids:
                notify_lost_user_ids_str = "{}".format(setting.notify_lost_user_ids.ids)
            setting.notify_lost_user_ids_str = notify_lost_user_ids_str

    @api.depends("lost_allowed_model_ids_str")
    def _compute_lost_allowed_model_ids(self):
        """ 
        Compute method for lost_allowed_model_ids 
        """
        for setting in self:
            lost_allowed_model_ids = []
            if setting.lost_allowed_model_ids_str:
                try:
                    notify_lost_users_list = safe_eval(setting.lost_allowed_model_ids_str)
                    lost_allowed_model_ids = self.env["ir.model"].search([("id", "in", notify_lost_users_list)]).ids
                except:
                    lost_allowed_model_ids = []
            setting.lost_allowed_model_ids = [(6, 0, lost_allowed_model_ids)]

    def _inverse_lost_allowed_model_ids(self):
        """
        Inverse method for lost_allowed_model_ids
        """
        for setting in self:
            lost_allowed_model_ids_str = ""
            if setting.lost_allowed_model_ids:
                lost_allowed_model_ids_str = "{}".format(setting.lost_allowed_model_ids.ids)
            setting.lost_allowed_model_ids_str = lost_allowed_model_ids_str

    notify_about_lost_messages = fields.Boolean(
        string="Lost messages notification",
        config_parameter="notify_about_lost_messages",
        help="If checked, a notification by each lost message will be sent to the chosen users",
    )
    notify_lost_user_ids = fields.Many2many(
        "res.users",
        string="Users to notify",
        compute=_compute_notify_lost_user_ids,
        inverse=_inverse_notify_lost_user_ids,
    )
    notify_lost_user_ids_str = fields.Char(string="Notify users (Str)", config_parameter="notify_lost_user_ids")
    lost_allowed_model_ids = fields.Many2many(
        "ir.model",
        string="Allowed Models",
        compute=_compute_lost_allowed_model_ids,
        inverse=_inverse_lost_allowed_model_ids,
    )
    lost_allowed_model_ids_str = fields.Char(string="Allowed models (Str)", config_parameter="lost_allowed_model_ids")
