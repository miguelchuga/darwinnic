from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class product_template(models.Model):
    _name = "product.bonification"
    _description = "Product bonification ranges"

    product_id = fields.Many2one('product.product', 'Product')
    minimum_qty = fields.Float('Minimum quantity')
    maximum_qty = fields.Float('Maximum quantity')
    bonus_qty = fields.Float('Bonus quantity')

    @api.constrains('minimum_qty')
    def _minimum_qty_constraint(self):
        for record in self:
            if record.minimum_qty <= 0:
                raise ValidationError(_('Minimum quantity must by greater than zero'))

    @api.constrains('maximum_qty')
    def _maximum_qty_constraint(self):
        for record in self:
            if record.maximum_qty <= 0:
                raise ValidationError(_('Maximum quantity must by greater than zero'))
            elif record.maximum_qty < record.minimum_qty:
                raise ValidationError(_('Maximum quantity must by greater than minimum quantity'))

    @api.constrains('bonus_qty')
    def _bonus_qty_constraint(self):
        for record in self:
            if record.bonus_qty <= 0:
                raise ValidationError(_('Bonus quantity must by greater than zero'))

class product_template2(models.Model):
    _name = "product.bonification.tipo"
    _description = "Product bonification tipo"

    product_id = fields.Many2one('product.product', 'Producto')
    x_tipo_id = fields.Many2one('x_tipo_cliente', 'Tipo cliente')