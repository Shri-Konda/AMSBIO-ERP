# -*-coding: utf-8 -*-

import logging
from datetime import datetime
from odoo import models, api, _


_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def write(self, vals):

        changed_fields = vals.keys()
        # Here we will track only one2many and many2many field as tracking of other fields is handled by Odoo
        xmany_fields = {}
        for field, attributes in self.fields_get(changed_fields).items():
            if attributes.get("type") in ["many2many", "one2many"]:
                xmany_fields.update({field: attributes.get("string")})
        old_values = {}
        for field, label in xmany_fields.items():
            old_values[field] = ",".join(self[field].mapped('display_name'))

        # update the record
        result = super(ProductTemplate, self).write(vals)

        # store new values
        new_values = {}
        for field, label in xmany_fields.items():
            new_values[field] = ",".join(self[field].mapped("display_name"))

        if xmany_fields:
            change_message = "<ul class='o_Message_trackingValues'>"
            for field, label in xmany_fields.items():
                if old_values.get(field) != new_values.get(field):
                    change_message += f"""<li><div class='o_Message_trackingValue'><div class="o_Message_trackingValueFieldName o_Message_trackingValueItem">{label}:</div> <div class="o_Message_trackingValueOldValue o_Message_trackingValueItem">{old_values.get(field)}</div> <div class="o_Message_trackingValueSeparator o_Message_trackingValueItem fa fa-long-arrow-right"></div> <div class="o_Message_trackingValueNewValue o_Message_trackingValueItem">{new_values.get(field)}</div></div></li>"""
            change_message += "</ul>"
            if "<li>" in change_message:
                self.message_post(body=_(change_message))
        return result

class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    def write(self, vals):
        """
        When supplierinfo is changed, changes will be logged into the product page.
        """

        self = self.sudo()

        old_values = {}
        if "price" in vals:
            old_values.update({'price': self.price})
        if "min_qty" in vals:
            old_values.update({'min_qty': self.min_qty})
        if "delay" in vals:
            old_values.update({'delay': self.delay})
        if "product_name" in vals:
            old_values.update({'product_name': self.product_name})
        if "product_code" in vals:
            old_values.update({'product_code': self.product_code})
        if "date_start" in vals:
            old_values.update({'date_start': self.date_start})
        if "date_end" in vals:
            old_values.update({'date_end': self.date_end})

        result = super(SupplierInfo, self).write(vals)
        # If pricelist is linked with some product and our fields are changed, we will log the changes on product form
        record = self.product_tmpl_id or self.product_id
        if old_values and record:
            message = record.message_post(body=_(f"Change in Vendor Pricelist: {self.name.name}"))
            for key, old_value in old_values.items():
                model = self.env["ir.model"].search([('model', '=', self._name)], limit=1)
                field = self.env["ir.model.fields"].search([('name', '=', key), ('model_id', '=', model.id)], limit=1)
                new_value = self[key]
                vals = {
                    'field': field.id,
                    'field_desc': field.field_description,
                    'field_type': field.ttype,
                }
                if field.ttype == "many2one":
                    vals.update({
                        'old_value_integer': old_value.id,
                        'new_value_integer': self.name.id,
                        'old_value_char': old_value.name,
                        'new_value_char': self.name.name
                    })
                elif field.ttype == "date":
                    vals.update({
                        'old_value_char': old_value or "",
                        'new_value_char': new_value or "",
                        'field_type': "char"
                    })
                else:
                    vals.update({
                        f'old_value_{field.ttype}': old_value,
                        f'new_value_{field.ttype}': new_value
                    })

                vals.update({'mail_message_id': message.id})
                tracking_value = self.env["mail.tracking.value"].create(vals)

        return result