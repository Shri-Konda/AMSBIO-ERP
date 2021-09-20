{
    'name': 'Update the purchase price based on the sales price',
    'version': '1.0',
    'category': 'Purchase',
    'summary': 'Update the purchase price based on the sales price',
    'description': """Update the purchase price based on the sales price.""",
    'sequence': 4,
    'depends': ['purchase', 'base_automation'],
    'data': [
        'views/company_view.xml',
        'data/automated_action_data.xml',
    ],
    'installable': True,
    'auto_install': False,
}
