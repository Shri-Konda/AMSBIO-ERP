# -*-coding: utf-8 -*-
{
    'name'      : "AMSBIO Receipt Warning",
    'summary'   : "Warning for immediate validation of receipt",
    'version'   : "16.0.1.0",
    'category'  : "Inventory/Inventory",
    'license'   : "Other proprietary",
    'author'    : "Target Integration",
    'website'   : "http://www.targetintegration.com",

    # modules necessary for this to work properly
    'depends'   : ["stock"],
    
    # always loaded data
    'data'      : ["wizard/stock_immediate_transfer_views.xml"],

}