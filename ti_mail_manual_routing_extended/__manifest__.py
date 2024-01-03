# -*-coding: utf-8 -*-
{
    'name'      : "Lost Message Routing Extended",
    'summary'   : "Fixes the routing of lost messages",
    'version'   : "16.0.1.0",
    'category'  : "Sales/Sales",
    'license'   : "Other proprietary",
    'author'    : "Target Integration",
    'website'   : "http://www.targetintegration.com",

    # any modules required for this to work properly
    'depends'   : ["mail_manual_routing", "sale", "crm"],

    # data always loaded
    'data'      : [
            "data/crons.xml",
            "views/sale_views.xml"
        ]
}