# -*-coding: utf-8 -*-
{
    'name'      : "Amsbio CRM Notifications",
    'summary'   : "CRM email notification automations",
    'version'   : "16.0.0.0",
    'category'  : "Sales/Sales",
    'license'   : "Other proprietary",
    'author'    : "Target Integration",
    'website'   : "http://www.targetintegration.com",

    # any modules required for this to work properly
    'depends'   : ["sale_stock", "crm"],

    # data always loaded
    'data'      : [
            "data/notification_crons.xml",
            "data/mail_templates.xml"
    ]
}