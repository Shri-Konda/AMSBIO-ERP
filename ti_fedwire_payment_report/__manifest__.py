# -*-coding: utf-8 -*-
{
    'name'      : "AMSBIO Fedwire Payment Report",
    'summary'   : "Print Fedwire Payment Report",
    'version'   : "16.0.1.0",
    'category'  : "Accounting/Accounting",
    'license'   : "Other proprietary",
    'author'    : "Target Integration",
    'website'   : "http://www.targetintegration.com",

    # modules necessary for this to work properly
    'depends'   : ["account"],
    
    # always loaded data
    'data'      : [
            "report/report_action.xml",
            "views/report_fedwire_payment.xml",
            "views/res_partner_views.xml",
            "data/action.xml"
        ],

    'application':  True,
    'installable':  True,
    'auto_install':  False,

}