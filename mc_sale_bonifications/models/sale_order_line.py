from odoo import models, fields, api, _

class sale_order(models.Model):
    _name = "sale.order"
    _inherit = "sale.order"

    def add_bonus_products(self,):
        if self.state == 'draft':
            
            self.env['sale.order.line'].search([('order_id', '=', self.id), ('bonus', '=', True)]).unlink()
            for line in self.order_line:
                line.write({'x_orden_id': line.id})
                if line.product_id.product_tmpl_id.has_bonus:
                    #bonificacion por tipo de cliente
                    _bono_por_producto = True
                    if line.product_id.product_tmpl_id.bonus_product_tipo_ids:
                        for bonus in line.product_id.product_tmpl_id.bonus_product_tipo_ids:
                             if self.x_tipo_cliente_id.id == bonus.x_tipo_id.id:
                                 for rango in bonus.x_tipo_id.x_tipo_cliente_bonificacion_ids:
                                     bonus_tipo = self.env['x_tipo_cliente_bonificacion'].browse([ rango.id ])
                                     if bonus_tipo.x_fecha_desde <= self.date_order <= bonus_tipo.x_fecha_hasta:
                                         if line.product_uom_qty >= bonus_tipo.x_desde and line.product_uom_qty <= bonus_tipo.x_hasta:
                                             self.env['sale.order.line'].create({
                                                 'order_id': self.id,
                                                 'product_id': bonus.product_id.id,
                                                 'name': bonus.product_id.name,
                                                 'product_uom': bonus.product_id.product_tmpl_id.uom_id.id,
                                                 'product_uom_qty': bonus_tipo.x_bonificacion,
                                                 'discount': 0,
                                                 'price_unit':  line.product_id.product_tmpl_id.price_for_bonus,
                                                 'bonus': True,
                                                 'maximum_bonus_qty': bonus_tipo.x_hasta,
                                                 'origin_line_id': line.id,
                                                 'x_orden_id':line.id,
                                                 'sequence':line.sequence,
                                             })
                                             _bono_por_producto = False                                             

                    if _bono_por_producto:
                        for bonus in line.product_id.product_tmpl_id.bonus_product_ids:
                            if line.product_uom_qty >= bonus.minimum_qty and line.product_uom_qty <= bonus.maximum_qty:
                                self.env['sale.order.line'].create({
                                    'order_id': self.id,
                                    'product_id': bonus.product_id.id,
                                    'name': bonus.product_id.name,
                                    'product_uom': bonus.product_id.product_tmpl_id.uom_id.id,
                                    'product_uom_qty': bonus.bonus_qty,
                                    'discount': 0,
                                    'price_unit':  line.product_id.product_tmpl_id.price_for_bonus,
                                    'bonus': True,
                                    'maximum_bonus_qty': bonus.bonus_qty,
                                    'origin_line_id': line.id,
                                    'x_orden_id':line.id,
                                    'sequence':line.sequence,
                                })

#    @api.model
#    def create(self, vals):
#        ret = super(sale_order, self).create(vals)
#        self.add_bonus_products(ret)
#        return ret

#    @api.multi
#    def write(self, vals):
#        ret = super(sale_order, self).write(vals)
#        for order in self:    
#            self.add_bonus_products(order)
#        return ret


class sale_order_line(models.Model):
    _name = "sale.order.line"
    _inherit = "sale.order.line"
    #_order = 'order_id, layout_category_id, sequence, id'
    _order = 'order_id, sequence, id'

    bonus = fields.Boolean('Bonus product')
    maximum_bonus_qty = fields.Float('Maximum bonus quantity')
    origin_line_id = fields.Many2one('sale.order.line', string='Origin bonus line')
    x_orden_id = fields.Integer(string='Order ID Mc')

    # @api.onchange('product_id', 'product_uom', 'product_uom_qty')
    # def _onchange_qty_bonus(self):
    #     if self.bonus:
    #         if self.product_uom_qty > self.maximum_bonus_qty:
    #             self.product_uom_qty = self.maximum_bonus_qty
    #     elif self.product_id.product_tmpl_id.has_bonus:
    #         for bonus in self.product_id.product_tmpl_id.bonus_product_ids:
    #             if self.product_uom_qty >= bonus.minimum_qty and self.product_uom_qty <= bonus.maximum_qty:
    #                 self.env['sale.order.line'].create({
    #                     'product_id': bonus.product_id.id,
    #                     'name': bonus.product_id.name,
    #                     'product_uom': bonus.product_id.product_tmpl_id.uom_id.id,
    #                     'product_uom_qty': bonus.bonus_qty,
    #                     'bonus': True,
    #                     'maximum_bonus_qty': bonus.bonus_qty,
    #                 })
