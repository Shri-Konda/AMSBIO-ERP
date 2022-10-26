# -*- coding: utf-8 -*-
{
    'name'      : "TI Sale Order Customisation",
    'author'    : "Target Integration",
    'summary'   : "All customisations related to sale order",
    'version'   : "14.0.0.2",
    'website'   : "http://www.targetintegration.com",
    'category'  : "Sales/Sales",

    # any modules necessary for this one to work
    'depends'   : ["base", "sale"],

    # always loaded
    'data'      : ["views/res_partner_views.xml"]
}
