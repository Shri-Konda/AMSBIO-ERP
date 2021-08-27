# -*- coding: utf-8 -*-

from odoo import models, fields, api


class my_module(models.Model):
    _name = 'my_module.my_module'
    _description = "This is a sample module, which will be used for holding custom templates in future."

    name = fields.Char()
    value = fields.Integer()
    description = fields.Text()
