# -*- coding: utf-8 -*-
import json
import copy
import base64
from odoo import fields, http, Command, tools, _
from odoo.tools.json import scriptsafe as json_scriptsafe
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.website_sale_product_configurator.controllers import main
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website.controllers.main import QueryURL
import logging
_logger = logging.getLogger(__name__)


class NewLead(http.Controller):

    @http.route(['/new/lead', '/new-lead-event'], type='http', auth="public", website=True)
    def ti_new_lead(self, **post):
        _logger.info(f"--------ti_new_lead------------{post}----------{request.httprequest.url_root, request.httprequest.query_string, request.httprequest.path, request.httprequest.host_url, request.httprequest.base_url}------")
        crm_tags = request.env["crm.tag"].sudo().search([("parent_id", "=", False)])
        child_crm_tags = request.env["crm.tag"].sudo().search([("parent_id", "!=", False)])
        new_lead_event = False
        redirect = "/new/lead/thankyou"
        action = "/new/lead"
        if '/new-lead-event' in request.httprequest.path:
            new_lead_event = True
            action = "/new-lead-event"
            redirect = "/new-lead-event/thankyou"
        if request.httprequest.method == 'POST' and post:
            lead = request.env["crm.lead"].sudo()
            create_vals = {}
            tag_id_list = []
            for key in post:
                if key in lead._fields:
                    create_vals.update({key: post.get(key)})
                else:
                    if "tag_id_" in key:
                        # tag_id_list.append(int(key.split("_")[-1]))
                        tag_id_list.append(int(post.get(key)))
            if tag_id_list:
                create_vals.update({"intrest_ids": [Command.set(tag_id_list)]})
            if create_vals:
                _logger.info(f"\n\n\n----------create_vals-----------{create_vals}---------{redirect}")
                lead.create(create_vals)
                return request.redirect(redirect)

        return request.env['ir.ui.view']._render_template("ti_website_crm_event_amsbio.ti_amsbio_crm_event_website_form", {
            "crm_tags": crm_tags,
            "child_crm_tags": child_crm_tags,
            "action": action,
            "name":request.env.user.name,
            "phone":request.env.user.phone,
            "email":request.env.user.email,
            "commercial_company_name":request.env.user.partner_id.commercial_company_name,
            "new_lead_event": new_lead_event,
            "events": request.env["event.event"].sudo().search([("website_published", "=", True)])
        })
    
    @http.route(['/new/lead/thankyou', '/new-lead-event/thankyou'], type='http', auth="public", website=True)
    def ti_new_lead_thank_you(self):
        return request.env['ir.ui.view']._render_template("ti_website_crm_event_amsbio.ti_amsbio_crm_event_website_thankyou", {})

