#!/usr/bin/python
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class account_journal(models.Model):

    _name = 'account.journal'
    _inherit = 'account.journal'


    #se sobre escribe el metodo para que no valide la numeracion de cheques del modulo accont_check_printing
    #@api.multi
##    def _set_check_next_number(self):
#        if self.check_next_number < self.check_sequence_id.number_next_actual:
#            raise ValidationError(_("The last check number was %s. In order to avoid a check being rejected "
#                "by the bank, you can only use a greater number.") % self.check_sequence_id.number_next_actual)
##        if self.check_sequence_id:
##            self.check_sequence_id.sudo().number_next_actual = self.check_next_number


    tipo_gasto = fields.Selection([('Bienes', 'Bienes'), ('Servicios',
                                  'Servicios')], 'Tipo Gasto')
    gravado = fields.Selection([('si', 'Si'), ('no', 'No')],
                               default='si')

    local = fields.Selection([('Local', 'Local'), ('Importacion',
                             'Importacion'),('Exportacion',
                             'Exportacion')], 'Local')
    #para neo farmacenter se creo el campo tipo_venta
#    tipo_venta = fields.Char('FC=Factura NC=Nota Credito', size=10)
    tipo_transaccion = fields.Char('Tipo transaccion', size=10)
    establecimiento = fields.Char('Establecimiento', size=10)
    asiste_libro = fields.Char('Código Asiste libro', size=10)
    imprime_libro = fields.Selection([('Si', 'Si')], 'Imprime en Libro '
            )
    serie_venta = fields.Char('Serie venta', size=30)
    tipo_venta = fields.Char('FC=Factura NC=Nota Credito', size=10)
    retencion_iva_cliente = fields.Selection([('Si', 'Si')],
            'Retención IVA - Cliente ')
    gface_electronico = fields.Boolean('Documento electronico GFACE ')

