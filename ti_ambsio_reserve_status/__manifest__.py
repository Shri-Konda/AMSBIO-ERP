# -*-coding: utf-8 -*-
{
    'name'      : "AMSBIO Delivery Order Reservation Status",
    'summary'   : "Shows products reservation status on delivery order",
    'version'   : "16.0.1.0",
    'category'  : "Inventory/Inventory",
    'license'   : "Other proprietary",
    'author'    : "Target Integration",
    'website'   : "http://www.targetintegration.com",

    # modules necessary for this to work properly
    'depends'   : ["stock"],
    
    # always loaded data
    'data'      : ["views/stock_picking_views.xml"],

    'application' :  True,
    'installable' :  True,
    'auto_install':  False,

}