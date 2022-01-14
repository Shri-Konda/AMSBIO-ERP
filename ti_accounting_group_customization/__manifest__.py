{
  "name"                 :  "Ti Accounting Group Customization",
  "summary"              :  """Accounting Group Customization.""",
  'category'             :  'Accounting/Accounting',
  "version"              :  "1.0.0",
  "sequence"             :  1,
  "author"               :  "Target Integration.",
  "website"              :  "http://www.targetintegration.com",
  "description"          :  """Accounting Group Customization""",
  "depends"              :  [
                             'account',
                            ],
  "data"                 :  [
                              'security/ir_group.xml',
                            ],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
}