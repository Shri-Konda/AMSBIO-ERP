
from odoo import models, fields, api,tools, _
from odoo import tools
import logging
_logger = logging.getLogger(__name__)



class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"


    
    def hide_ti_menus_to_user(self, menu_data):
        """ Return the ids of the menu items hide to the user. """
        menu_ids = []
        
        if self.env.user.sudo().has_group('ti_accounting_group_customization.group_user_2'):
            try:
                
                accounting_menu = self.env.ref('account.menu_finance_entries').id
                dashboard_menu = self.env.ref('account.menu_board_journal_1').id
                # reporting_menu = self.env.ref('account.menu_finance_reports').id
                configuration_menu = self.env.ref('account.menu_finance_configuration').id
                
                menu_ids.extend([dashboard_menu,accounting_menu,configuration_menu])
            except Exception as e:
                _logger.info("~~~~~~~~~~Exception~~~~~~~~%r~~~~~~~~~~~~~~~~~",e)
                pass
        return menu_ids



    @api.model
    @tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'debug')
    def _visible_menu_ids(self, debug=False):
        """ Return the ids of the menu items visible to the user. """
        res = super(IrUiMenu, self)._visible_menu_ids(debug=debug)

        to_remove_menu_ids = self.hide_ti_menus_to_user(menu_data=res)
        res = res - set(to_remove_menu_ids)

        return res



class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'


    @tools.ormcache('self.env.uid', 'self.env.su')
    def _get_tracked_fields(self):
        """ Return the set of tracked fields names for the current model. """
        if self.__class__.__name__=='product.template':
            remove_fields = ('write_date','message_unread','create_uid','__last_update','activity_exception_icon','activity_summary','create_date','activity_type_icon','message_is_follower','write_uid','message_follower_ids','message_unread_counter','activity_type_id','activity_state')
            
            fields = {
                name
                for name, field in self._fields.items()
                if name not in remove_fields
            }
            return fields and set(self.fields_get(fields))
        else:
            return super(MailThread, self)._get_tracked_fields()
        
