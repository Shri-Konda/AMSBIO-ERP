# -*-coding: utf-8 -*-
{
    'name'      : "Amsbio Purchase Warning",
    'summary'   : "Raise purchase warning for suppliers when RFQ is confirmed",
    'version'   : "16.0.0.0",
    'category'  : "Sales/Sales",
    'license'   : "Other proprietary",
    'author'    : "Target Integration",
    'website'   : "http://www.targetintegration.com",

    # any modules required for this to work properly
    'depends'   : ["purchase"],

    # data always loaded
    'data'      : [
            "security/ir.model.access.csv",
            "wizard/amsbio_purchase_warn_views.xml"
    ]
}