# -*-coding: utf-8 -*-
{
    'name': "TI Receipt Warning",
    'author': "Target Integration",
    'summary': "Warning for Receipts Immediate Transfer",
    'version': "1.0", 
    'category': "Uncategorized",
    'website': "http://www.targetintegration.com",
    # any module require for this one to work properly
    'depends': ["base", "stock"],
    'data': [
        'wizard/stock_immediate_transfer_views.xml'
    ]
}