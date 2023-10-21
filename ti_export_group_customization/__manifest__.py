# -*-coding: utf-8 -*-
{
    'name'      : "AMSBIO Delete Export Templates",
    'summary'   : "Restrict normal user from deleting saved export templates",
    'version'   : "16.0.0.0",
    'category'  : "Accounting/Accounting",
    'license'   : "Other proprietary",
    'author'    : "Target Integration",
    'website'   : "http://www.targetintegration.com",

    # modules necessary for this to work properly
    'depends'   : ["web"],

    # data and views
    'data'      : ["security/ir_group.xml"],

    'assets'    : {
        'web.assets_backend': ["ti_export_group_customization/static/src/xml/inherit_base.xml"]
    },
    'application' :  True,
    'installable' :  True,
    'auto_install':  False,
}