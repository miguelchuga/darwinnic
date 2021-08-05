# -*- coding: utf-8 -*- 
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}
# Since invoice amounts are unsigned, this is how we know if money comes in or goes out
MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': 1,
    'in_invoice': -1,
    'out_refund': -1,
}

class MultiInvoicePayment(models.TransientModel):
    _name="customer.multi.payments"
    # _inherit = 'account.payment.register'

    memo = fields.Char(string='Memo')
    payment_date = fields.Date(required=True, default=fields.Date.context_today)
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Internal Transfer')], string='Payment Type', required=True, readonly=True, default="outbound")
    journal_id = fields.Many2one('account.journal', required=True, domain=[('type', 'in', ('bank', 'cash'))])
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method Type', required=True,
                                        help="Manual: Get paid by cash, check or any other method outside of Odoo.\n"
                                        "Electronic: Get paid automatically through a payment acquirer by requesting a transaction on a card saved by the customer when buying or subscribing online (payment token).\n"
                                        "Check: Pay bill by check and print it from Odoo.\n"
                                        "Batch Deposit: Encase several customer checks at once by generating a batch deposit to submit to your bank. When encoding the bank statement in Odoo, you are suggested to reconcile the transaction with the batch deposit.To enable batch deposit, module account_batch_payment must be installed.\n"
                                        "SEPA Credit Transfer: Pay bill from a SEPA Credit Transfer file you submit to your bank. To enable sepa credit transfer, module account_sepa must be installed ")
    final_amount = fields.Float(string='Total Amount', \
        compute='_final_amount',store=True)
    is_customer = fields.Boolean(string="Is Customer")
    customer_invoice_ids = fields.One2many('customer.invoice.lines','customer_wizard_id')
    supplier_invoice_ids = fields.One2many('supplier.invoice.lines','supplier_wizard_id')
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')])

    @api.model
    def _compute_payment_amount(self, invoices, currency, journal, date=None):
        '''Compute the total amount for the payment wizard.

        :param invoices:    Invoices on which compute the total as an account.invoice recordset.
        :param currency:    The payment's currency as a res.currency record.
        :param journal:     The payment's journal as an account.journal record.
        :param date:        The payment's date as a datetime.date object.
        :return:            The total amount to pay the invoices.
        '''
        company = journal.company_id
        currency = currency or journal.currency_id or company.currency_id

        date = date or fields.Date.context_today

        if not invoices:
            return 0.0

        self.env['account.move'].flush(['type', 'currency_id'])
        self.env['account.move.line'].flush(['amount_residual', 'amount_residual_currency', 'move_id', 'account_id'])
        self.env['account.account'].flush(['user_type_id'])
        self.env['account.account.type'].flush(['type'])
        self._cr.execute('''
            SELECT
                move.type AS type,
                move.currency_id AS currency_id,
                SUM(line.amount_residual) AS amount_residual,
                SUM(line.amount_residual_currency) AS residual_currency
            FROM account_move move
            LEFT JOIN account_move_line line ON line.move_id = move.id
            LEFT JOIN account_account account ON account.id = line.account_id
            LEFT JOIN account_account_type account_type ON account_type.id = account.user_type_id
            WHERE move.id IN %s
            AND account_type.type IN ('receivable', 'payable')
            GROUP BY move.id, move.type
        ''', [tuple(invoices.ids)])
        query_res = self._cr.dictfetchall()

        total = 0.0
        for res in query_res:
            move_currency = self.env['res.currency'].browse(res['currency_id'])
            if move_currency == currency and move_currency != company.currency_id:
                total += res['residual_currency']
            else:
                total += company.currency_id._convert(res['amount_residual'], currency, company, date)
        return total

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            if self.journal_id.currency_id:
                self.currency_id = self.journal_id.currency_id

            # Set default payment method (we consider the first to be the default one)
            payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
            payment_methods_list = payment_methods.ids

            default_payment_method_id = self.env.context.get('default_payment_method_id')
            if default_payment_method_id:
                # Ensure the domain will accept the provided default value
                payment_methods_list.append(default_payment_method_id)
            else:
                self.payment_method_id = payment_methods and payment_methods[0] or False

            # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
            payment_type = self.payment_type in ('outbound', 'transfer') and 'outbound' or 'inbound'

            domain = {'payment_method_id': [('payment_type', '=', payment_type), ('id', 'in', payment_methods_list)]}

            return {'domain': domain}
        return {}



    @api.depends("customer_invoice_ids","supplier_invoice_ids")
    def _final_amount(self):
        for amount in self:
            total = 0
            if amount.customer_invoice_ids:
                for i in amount.customer_invoice_ids:
                    total += i.amount_to_pay
                amount.update({
                    'final_amount' : total
                })
            if amount.supplier_invoice_ids:
                for i in amount.supplier_invoice_ids:
                    total += i.amount_to_pay
                amount.update({
                    'final_amount' : total
                })
                
            
    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if self.payment_type:
            return {'domain': {'payment_method_id': [('payment_type', '=', self.payment_type)]}}

    def _get_invoices(self):
        return self.env['account.move'].browse(self._context.get('active_ids',[]))

    @api.model
    def default_get(self, fields):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        invoices = self.env[active_model].browse(active_ids)

        if any((invoice.state != 'posted' or invoice.invoice_payment_state not in ['not_paid','in_payment']) for invoice in invoices):
            raise UserError(_("You can only register payments for posted"
                              " invoices"))

        if any(MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type] != MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type]
               for inv in invoices):
            raise UserError(_("You cannot mix customer invoices and vendor"
                              " bills in a single payment."))
            
        if any(inv.currency_id != invoices[0].currency_id for inv in invoices):
            raise UserError(_("In order to pay multiple invoices at once, they"
                              " must use the same currency."))

        rec = {}
        inv_list = []
        if MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type] == 'customer':
            for inv in invoices:
                inv_list.append((0,0,{
                    'invoice_id' : inv.id,  
                    'partner_id' : inv.partner_id.commercial_partner_id.id,
                    'total_amount' : inv.amount_total or 0.0,
                    'payment_diff' : inv.amount_residual or 0.0,
                    'amount_to_pay' : inv.amount_residual or 0.0,
                    }))
            rec.update({'customer_invoice_ids':inv_list,'is_customer':True})
        if MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type] == 'supplier':
            for inv in invoices:
                inv_list.append((0,0,{
                    'invoice_id' : inv.id,  
                    'partner_id' : inv.partner_id.commercial_partner_id.id,
                    'total_amount' : inv.amount_total or 0.0,
                    'payment_diff' : inv.amount_residual or 0.0,
                    'amount_to_pay' : inv.amount_residual or 0.0,
                    }))
            rec.update({'supplier_invoice_ids':inv_list,'is_customer':False})
            
        total_amount = sum(inv.amount_residual * MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.type] for inv in invoices)
        # communication = ' '.join([ref for ref in invoices.mapped('reference') if ref])
        
        amount = self._compute_payment_amount(invoices, invoices[0].currency_id, invoices[0].journal_id)
        rec.update({
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'payment_type' : 'inbound' if amount > 0 else 'outbound',
        })
        return rec

    def get_new_payment_vals(self,payment):
        invoices = self.env['account.move'].browse(payment['invoice_list'])

        values = {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': self.memo+" Documentos: "+" ".join(i.invoice_payment_ref or " "+i.ref or i.name for i in invoices),
            'invoice_ids': [(6, 0, payment['invoice_list'])],
            'payment_type': self.payment_type,
            'amount': abs(payment['final_total']),
            'currency_id': invoices[0].currency_id.id,
            'partner_id': invoices[0].commercial_partner_id.commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'partner_bank_account_id': invoices[0].invoice_partner_bank_id.id,
        }


        return values                                                          

    def register_multi_payment(self):
        if self.customer_invoice_ids:
            for amount in self.customer_invoice_ids:
                if not amount.amount_to_pay > 0.0:
                    raise UserError(_("Amount must be strictly positive \n"
                                    "Enter Receive amount"))
        elif self.supplier_invoice_ids:
            for amount in self.supplier_invoice_ids:
                if not amount.amount_to_pay > 0.0:
                    raise UserError(_("Amount must be strictly positive \n"
                                    "Enter Receive amount"))
        else:
            raise UserError(_("Something vent wrong.... \n"))


        data = {}
        context = {}
        
        active_model = self._context.get('active_model')
        active_ids = self._context.get('active_ids')
        invoices = self.env[active_model].browse(active_ids)


        if self.is_customer:
            for inv in self.customer_invoice_ids:
                context.update({'is_customer':True})

                inv.payment_diff = inv.invoice_id.amount_residual - inv.amount_to_pay
                
                partner_id = str(inv.invoice_id.partner_id.commercial_partner_id.id)
                if partner_id in data:
                    old_payment = data[partner_id]['final_total']
                    final_total = old_payment + inv.amount_to_pay

                    data[partner_id].update({
                                'partner_id': partner_id,
                                'final_total' : final_total,
                                'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[inv.invoice_id.type],
                                'payment_method_id': inv.payment_method_id,
                                'invoice_list' : data[partner_id]['invoice_list'] + [inv.invoice_id.id]
                                })
                    data[partner_id]['inv_val'].update({
                        str(inv.invoice_id.id) :{
                        'amount_to_pay' : inv.amount_to_pay,
                        'payment_diff' : inv.payment_diff,
                        }})
                else:
                    data.update({ partner_id : {
                        'invoice_id' : inv.id,
                        'partner_id' : inv.partner_id.commercial_partner_id.id,
                        'total_amount' : inv.total_amount,
                        'final_total' : inv.amount_to_pay,
                        'invoice_list' : [inv.invoice_id.id],
                        'inv_val' : { str(inv.invoice_id.id) : {
                            'amount_to_pay' : inv.amount_to_pay,
                            'payment_diff' : inv.payment_diff,
                            }}
                        }})
        else:
            for inv in self.supplier_invoice_ids:
                context.update({'is_customer':False})
                partner_id = str(inv.invoice_id.partner_id.commercial_partner_id.id)              
                if partner_id in data:
                    old_payment = data[partner_id]['final_total']
                    final_total = old_payment + inv.amount_to_pay
                    data[partner_id].update({
                                'partner_id': partner_id,
                                'final_total' : final_total,
                                'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[inv.invoice_id.type],
                                'payment_method_id': inv.payment_method_id,
                                'invoice_list' : data[partner_id]['invoice_list'] + [inv.invoice_id.id]
                                })
                    data[partner_id]['inv_val'].update({
                            str(inv.invoice_id.id) :{
                                'amount_to_pay' : inv.amount_to_pay,
                            }
                        })
                else:
                    data.update({ partner_id : {
                        'invoice_id' : inv.id,
                        'partner_id' : inv.partner_id.commercial_partner_id.id,
                        'total_amount' : inv.total_amount,
                        'final_total' : inv.amount_to_pay,
                        'invoice_list' : [inv.invoice_id.id],
                        'inv_val' : { str(inv.invoice_id.id) : {
                            'amount_to_pay' : inv.amount_to_pay,
                            }}
                        }})

        context.update({'payment':data})

        for payment in list(data):
            payment_ids = self.env['account.payment'].create(self.get_new_payment_vals(payment=data[payment]))
            payment_ids.with_context(payment=context).post()

class InvoiceLines(models.TransientModel):
    _name = 'customer.invoice.lines'

    customer_wizard_id = fields.Many2one('customer.multi.payments')
    invoice_id = fields.Many2one('account.move',required=True,
        string="Invoice Numbers")
    partner_id = fields.Many2one('res.partner',string='Customer',
        related='invoice_id.partner_id', 
        store=True, readonly=True, related_sudo=False)
    payment_method_id = fields.Many2one('account.payment.method',string='Payment Type')
    total_amount = fields.Float("Invoice Amount", required=True)
    amount_to_pay = fields.Float(string='Receive Amount')
    payment_diff = fields.Float(string='Residual Amount',store=True,readonly=True)

class InvoiceLines(models.TransientModel):
    _name = 'supplier.invoice.lines'

    supplier_wizard_id = fields.Many2one('customer.multi.payments')
    invoice_id = fields.Many2one('account.move',required=True,
        string="Bill Numbers")
    partner_id = fields.Many2one('res.partner',string='Vendor',
        related='invoice_id.partner_id', 
        store=True, readonly=True, related_sudo=False)
    payment_method_id = fields.Many2one('account.payment.method',string='Payment Type')
    total_amount = fields.Float("Invoice Amount", required=True)
    payment_diff = fields.Float(string='Residual Amount',store=True,readonly=True)
    amount_to_pay = fields.Float(string='Receive Amount')
