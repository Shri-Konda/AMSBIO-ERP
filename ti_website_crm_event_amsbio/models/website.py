# -*- coding: utf-8 -*-

import logging
from odoo.addons.website.controllers.main import QueryURL

from fnmatch import translate

from odoo import api, fields, models, tools, SUPERUSER_ID, _

_logger = logging.getLogger(__name__)
