# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class pos_order_fel(models.Model):
    _name = "pos.order"
    _inherit = "pos.order"

    infilefel_comercial_name = fields.Char(string='Comercial name' )
    serie_venta = fields.Char('Serie ventas')
    infilefel_establishment_street = fields.Char('Establishment street')


    nit_certificador = fields.Char('Nit empresa certificadora')
    nombre_certificador = fields.Char('Nombre empresa certificadora ')
    frase_certificador = fields.Char('Frase empresa o cliente')


    nit_empresa = fields.Char('Nit empresa')
    nombre_empresa = fields.Char('Nombre empresa')

    infile_number = fields.Char('Número DTE')
    infilefel_sat_uuid = fields.Char('SAT UUID')
    infilefel_sign_date = fields.Datetime('Sign date')

    nombre_cliente = fields.Char('Nombre cliente')
    nit = fields.Char('Nit cliente')
    direccion_cliente = fields.Char('Dirección cliente')
    fecha_factura = fields.Char('Fecha factura')


    caja = fields.Char('Caja')
    vendedor = fields.Char('Vendedor')
    forma_pago = fields.Char('Forma pago')



#    @api.model
#    def create(self, values):
#        ret = super(pos_order_fel, self).create(values)
#        ret.infilefel_comercial_name = 'miguel antonio chuga martinez'
#        return ret