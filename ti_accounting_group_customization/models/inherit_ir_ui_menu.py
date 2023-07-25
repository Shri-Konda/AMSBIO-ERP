# -*- coding: utf-8 -*-

import logging
from odoo import models, api, tools


_logger = logging.getLogger(__name__)

class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    def _menus_to_hide_from_group_user2(self):
        """ Return the ids of the menu items hide to the user. """

        menus = set()
        try:
            accounting_menu = self.env.ref('account.menu_finance_entries')
            dashboard_menu = self.env.ref('account.menu_board_journal_1')
            reporting_menu = self.env.ref('account.menu_finance_reports')
            configuration_menu = self.env.ref('account.menu_finance_configuration')
            menus.add(accounting_menu.id)
            menus.add(dashboard_menu.id)
            menus.add(reporting_menu.id)
            menus.add(configuration_menu.id)
        except Exception as e:
            _logger.error(f"\n==>error when hiding menus from group user 2: {e}")
        finally:
            return menus

    @api.model
    @tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'debug')
    def _visible_menu_ids(self, debug=False):
        "override method to hide few menus from group user 2"

        visible_menus = super(IrUiMenu, self)._visible_menu_ids(debug=debug)
        # _logger.info(f"\n==>visible_menus: {visible_menus}")
        if self.env.user.has_group('ti_accounting_group_customization.group_user_2'):
            menus_to_hide = self._menus_to_hide_from_group_user2()
            # _logger.info(f"\n==>menus_to_hide: {menus_to_hide}")
            if menus_to_hide:
                visible_menus = visible_menus - menus_to_hide

        return visible_menus
