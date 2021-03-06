{
  "name"                 :  "TI Warehouse count",
  "summary"              :  """TI-Warehouse Count.""",
  "category"             :  "Inventory/Inventory",
  "version"              :  "1.0.25",
  "sequence"             :  1,
  "author"               :  "Target Integration.",
  "website"              :  "http://www.targetintegration.com",
  "description"          :  """Count Warehouse product quantity with odoo""",
  "depends"              :  [
                             'base_automation',
                             'sale_management',
                             'stock',
                             'sale_purchase_inter_company_rules',
                            ],
  "data"                 :  [
                              
                              'views/inherit_sale_order_line.xml',
                              'report/report_action.xml',
                              'views/inherit_res_config_setting.xml',
                              'views/inherit_stock_backorder_confirmation.xml',
                              'views/report_bacs_payment.xml',
                              'data/action.xml',
                            ],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
}
