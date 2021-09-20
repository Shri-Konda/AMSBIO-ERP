from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    po_line_discount = fields.Float("PO Line Discoust(%)")
