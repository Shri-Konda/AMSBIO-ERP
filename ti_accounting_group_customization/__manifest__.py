{
  "name"                 :  "Ti Accounting Group Customization",
  "summary"              :  """Accounting Group Customization.""",
  'category'             :  'Accounting/Accounting',
  "version"              :  "1.0.2",
  "sequence"             :  1,
  "author"               :  "Target Integration.",
  "website"              :  "http://www.targetintegration.com",
  "description"          :  """Accounting Group Customization""",
  "depends"              :  [
                             'account_accountant',
                            ],
  "data"                 :  [
                              'security/ir_group.xml',
                              'views/group_user_views.xml'
                            ],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
}