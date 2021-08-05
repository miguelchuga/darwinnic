# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from . import util

class account_payment(models.Model):
    
    _name = 'account.payment'
    _inherit = 'account.payment'


    #@api.one
    def _calcular_letras(self):
        self.numeros_a_letras =  util.num_a_letras(self.amount)

    #@api.one
    def _calcular_letras_dolar(self):
        self.numeros_a_letras_dolar =  util.num_a_letras_dolar(self.amount)

    @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
    def _compute_destination_account_id(self):
        for payment in self:
            if payment.invoice_ids:
                payment.destination_account_id = payment.invoice_ids[0].mapped(
                    'line_ids.account_id').filtered(
                        lambda account: account.user_type_id.type in ('receivable', 'payable'))[0]
            elif payment.payment_type == 'transfer':
                if not payment.company_id.transfer_account_id.id:
                    raise UserError(_('There is no Transfer Account defined in the accounting settings. Please define one to be able to confirm this transfer.'))
                payment.destination_account_id = payment.company_id.transfer_account_id.id
            elif payment.partner_id:
                if payment.partner_type == 'customer':
                    payment.destination_account_id = payment.partner_id.property_account_receivable_id.id
                else:
                    if self.x_account_id:
                        payment.destination_account_id = self.x_account_id.id
                    else:
                        payment.destination_account_id = self.partner_id.property_account_payable_id.id
            elif payment.partner_type == 'customer':
                if self.x_account_id:
                    default_account = self.x_account_id.id
                    payment.destination_account_id = self.x_account_id.id
                else:
                    default_account = self.env['ir.property'].get('property_account_receivable_id', 'res.partner')
                    payment.destination_account_id = default_account.id
            elif payment.partner_type == 'supplier':
                if self.x_account_id:
                    payment.destination_account_id = self.x_account_id.id
                else:
                    default_account = self.env['ir.property'].get('property_account_payable_id', 'res.partner')
                    if default_account:
                        payment.destination_account_id = default_account.id



    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if not self.x_account_id and self.payment_type == 'outbound':
            self.x_account_id = self.partner_id.property_account_payable_id.id

    #@api.multi
    def unlink(self):
        if any(bool(rec.move_line_ids) for rec in self):
            raise UserError(_("You can not delete a payment that is already posted"))
        if self.ids:
            for i in self.ids:
                _payment_id = self.env['account.payment'].browse(i)
                if _payment_id.state == 'draft':
                    _payment_id.write({'move_name':""}) 
                    print(_payment_id.move_name)

        return super(account_payment, self).unlink()


    numeros_a_letras = fields.Char('Letras', compute=_calcular_letras)
    numeros_a_letras_dolar = fields.Char('Letras dolar', compute=_calcular_letras_dolar)


    x_recibo_caja = fields.Char('Recibo de caja')
    x_deposito = fields.Char('No. deposito')
    numeros_a_letras = fields.Char('Letras', compute=_calcular_letras)
    x_no_negociable = fields.Boolean('NO NEGOCIABLE : ', default=True )
    x_account_id = fields.Many2one('account.account', string='Cuenta')
    x_fecha_recibo = fields.Date(string='Fecha recibo', copy=False)
    x_emitir_otro = fields.Char(string='Emitir cheque a ')