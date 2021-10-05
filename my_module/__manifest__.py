# -*- coding: utf-8 -*-
{
    'name': "Custom templates",

    'summary': """
        A custom module to update legacy pdf reports""",

    'description': """
        This module inherits legacy pdf reports and update them to company's default pdf report
    """,

    'author': "Vaibhavnath Jha",
    'website': "",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'views/OrderQuotationTemplate.xml',
    ],
}
