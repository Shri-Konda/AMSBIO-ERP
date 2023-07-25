# -*-coding: utf-8 -*-
{
    'name'      : "AMSBIO Accounting Groups Customisation",
    'summary'   : "Adds new accounting user groups",
    'version'   : "16.0.1.0",
    'sequence'  :  1,
    'category'  : "Accounting/Acccounting",
    'license'   : "Other proprietary",
    'author'    : "Target Integration",
    'website'   : "http://www.targetintegration.com",

    # modules necessary for this to work properly
    'depends'   : ["account_accountant"],

    # data and views
    'data'      : [
                "security/ir_group.xml",
                "views/group_user_views.xml"
    ],
    'application' :  True,
    'installable' :  True,
    'auto_install':  False,

}