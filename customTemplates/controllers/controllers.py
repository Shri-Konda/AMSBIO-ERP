# -*- coding: utf-8 -*-
from odoo import http


class customTemplate(http.Controller):
    @http.route('/customTemplates/customTemplates/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/customTemplates/customTemplates/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('customTemplates.listing', {
            'root': '/customTemplates/customTemplates',
            'objects': http.request.env['customTemplates.customTemplates'].search([]),
        })

    @http.route('/customTemplates/customTemplates/objects/<model("customTemplates.customTemplates"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('customTemplates.object', {
            'object': obj
        })
