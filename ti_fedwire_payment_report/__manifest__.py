{
  "name"                 :  "TI Fedwire Payment report.",
  "summary"              :  """TI Fedwire Payment Report.""",
  'category'             :  'Accounting/Accounting',
  "version"              :  "1.0.1",
  "sequence"             :  1,
  "author"               :  "Target Integration.",
  "website"              :  "http://www.targetintegration.com",
  "description"          :  """TI Fedwire Payment Report""",
  "depends"              :  [
                             'account',
                            ],
  "data"                 :  [
                              'report/report_action.xml',
                              'views/report_fedwire_payment.xml',
                              'data/action.xml',
                            ],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
}