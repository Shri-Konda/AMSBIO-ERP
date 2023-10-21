# -*-coding: utf-8 -*-
{
    'name'      : "AMSBIO Inter-Company Sales/Purchases Orders Support",
    'summary'   : "AMSBIO customizations related to inter-company sales/purchases, BACS Payment and warehouse count",
    'version'   : "16.0.1.0",
    'category'  : "Inventory/Inventory",
    'license'   : "Other proprietary",
    'author'    : "Target Integration",
    'website'   : "http://www.targetintegration.com",

    # modules necessary for this to work properly
    'depends'   : ["base_automation", "sale_stock", "sale_purchase_inter_company_rules"],
    
    # always loaded data
    'data'      : [
            'views/inherit_sale_order_line.xml',
            'report/report_action.xml',
            'views/inherit_res_config_setting.xml',
            'views/inherit_stock_backorder_confirmation.xml',
            'views/report_bacs_payment.xml',
            'data/action.xml',
        ],

    'application':  True,
    'installable':  True,
    'auto_install':  False,

}