from odoo import models, fields, api, _

class product_template(models.Model):
    _name = "product.template"
    _inherit = "product.template"

    has_bonus = fields.Boolean('Has bonus')
    price_for_bonus = fields.Float('Price for bonus')

    bonus_product_ids = fields.Many2many('product.bonification', string='Bonification products')
    bonus_product_tipo_ids = fields.Many2many('product.bonification.tipo', string='Bonification productos tipo')