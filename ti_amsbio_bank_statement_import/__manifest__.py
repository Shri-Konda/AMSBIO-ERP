# -*-coding: utf-8 -*-
{
    'name'      : "AMSBIO Import Bank Statements",
    'summary'   : "Upload bank statements in custom csv format and create bank statements",
    'version'   : "16.0.1.0",
    'category'  : "Accounting",
    'license'   : "Other proprietary",
    'author'    : "Target Integration",
    'website'   : "http://www.targetintegration.com",

    # modules necessary for this to work properly
    'depends'   : ["account_bank_statement_import_csv"],

    # data and views
    'data'      : [
                "security/ir.model.access.csv",
                "security/security.xml",
                "views/bank_statement_import_template_views.xml",
                "views/account_journal_views.xml"
    ]
}