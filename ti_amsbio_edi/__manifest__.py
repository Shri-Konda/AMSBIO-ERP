# -*-coding: utf-8 -*-
{
    'name'      : "Amsbio EDI Integration",
    'summary'   : "EDI Integration of Odoo and third party to exchange orders, delivery, and invoice data through FTP",
    'version'   : "16.0.4.1",
    'category'  : "Sales/Sales",
    'license'   : "Other proprietary",
    'author'    : "Target Integration",
    'website'   : "http://www.targetintegration.com",

    # any modules required for this to work properly
    'depends'   : ["sale", "stock", "ti_warehouse_count", "sale_purchase_inter_company_rules"],

    # data always loaded
    'data'      : [
                "security/ir.model.access.csv",
                "data/edi_crons.xml",
                "data/edit_data.xml",
                "views/ftp_server_views.xml",
                "views/sale_order_views.xml",
                "views/stock_picking_views.xml",
                "views/account_move_views.xml",
                "wizard/select_edi_order_views.xml"
    ],
    'external_dependencies': {
        'python': ["paramiko"]
    }
}