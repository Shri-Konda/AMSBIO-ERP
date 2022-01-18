# -*-coding: utf-8 -*-
{
    'name': "Delivery Orders Reserve Status",
    'author': "Target Integration",
    'summary': "Displays Status of Reserved Quantities",
    'version': "1.0.4",
    'website': "http://www.targetintegration.com",
    'depends': ["base", "stock"],
    'data': [
        'views/stock_picking_views.xml'
    ],
    "application"          :  True,
     "installable"          :  True,
     "auto_install"         :  False,
}
