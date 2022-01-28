{
  "name"                 :  "Ti Export Group Customization",
  "summary"              :  """Export Group Customization.""",
  'category'             :  'Accounting/Accounting',
  "version"              :  "1.0.1",
  "sequence"             :  1,
  "author"               :  "Target Integration.",
  "website"              :  "http://www.targetintegration.com",
  "description"          :  """Export Group Customization""",
  "depends"              :  [
                             'web',
                            ],
  "qweb"                 :  [
                              "static/src/xml/inherit_base.xml",
                            ],
  "data"                 :  [ "security/ir_group.xml", ],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
}