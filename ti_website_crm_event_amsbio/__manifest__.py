# -*- coding: utf-8 -*-


{
    'name': 'Amsbio Website CRM Event Customizations',
    'license': 'Other proprietary',
    'summary': """Custom module for Amsbio customizations.""",
    'description': """ Custom module for Amsbio customizations """,
    'author': "Target Integartion",
    'version': '16.0.1.0.0',
    'category' : 'CRM/Website',
    'depends': ['sales_team', "crm", "website_event"],
    'data':[
        'views/models_views.xml',
        'views/website_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ti_website_crm_event_amsbio/static/src/js/intrest.js',
        ],
    },
    'installable' : True,
    'application' : False,
}
