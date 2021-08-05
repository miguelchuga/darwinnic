# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from . import util

class account_move(models.Model):

    _name = 'account.move'
    _inherit = 'account.move'

    #@api.one
    def _calcular_letras(self):
        self.numeros_a_letras =  util.num_a_letras(self.amount_total)


    #@api.one
    def _calcular_letras_dolar(self):
        self.numeros_a_letras_dolar =  util.num_a_letras_dolar(self.amount_total)

    serie_gt = fields.Char('Serie de la factura', size=40)
    numeros_a_letras = fields.Char('Letras', compute=_calcular_letras)
    numeros_a_letras_dolar = fields.Char('Letras', compute=_calcular_letras_dolar)


class account_invoice_line(models.Model):
    _name = 'account.move.line'
    _inherit = 'account.move.line'

    @api.depends('quantity', 'price_unit')
    def _n_total_linea(self):
        for line in self:
            line.n_total_linea = line.quantity * line.price_unit


    n_total_linea = fields.Float('Total linea', compute=_n_total_linea)

#    @api.constrains('line_ids', 'journal_id', 'auto_reverse', 'reverse_date')
#    def _validate_move_modification(self):
#        print('Se quita esta validación porque en el caso de los cheques en algunos casos se agregan cuentas a la partida del cheque en account_move.')
#        if 'posted' in self.mapped('line_ids.payment_id.state'):
#            raise ValidationError(_("You cannot modify a journal entry linked to a posted payment."))