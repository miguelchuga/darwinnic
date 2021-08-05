# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd. (<http://devintellecs.com>).
#
##############################################################################
from openerp import models, fields, api, _
from openerp.osv import osv
from datetime import datetime as dt
import time
from openerp.exceptions import Warning
from datetime import date

class bank_reconciliation(models.Model):

    _name="bank.reconciliation"
    
    name=fields.Char(string='Reference',required="1",default="")
    account_rec_id=fields.Many2one('account.account',string='Account')
    journal_id=fields.Many2one('account.journal',string='Journal')
    journal_op_id=fields.Many2one('account.journal',string='2nd Journal')
    start_balance=fields.Float(string='Starting Balance')
    end_balance=fields.Float(string='Ending Balance',required="1")
    journal_entry_ids = fields.Many2many('account.move.line', 'account_move_line_rel','journal_ids','move_ids',string="Journal Entries")
    state=fields.Selection([('draft','Draft'),('close','Close')],string='State',default="draft")
    start_date = fields.Date(string='Start Date',required="1",default=date(date.today().year, 1, 1))
    end_date = fields.Date(string='End Date',required="1")
    bank_statement=fields.Float(string='Balance as per bank statement', compute='_compute_bank_statement')
    bank_account=fields.Float(string='Balance as per bank account',compute='_compute_bank_account')
    less_unrepresented_amount=fields.Float(string='Less Unrepresented Amount', compute='_compute_unrepresented_amount')
    deposit_not_credited_bank=fields.Float(string='Add deposit not credited by bank',compute='_compute_credited_bank')
    differance =fields.Float(string='Differance' , compute='_compute_differance')
    
    
    def action_confirm(self):
        
        # Marca registro de conciliación bancaria (bank_reconciliation) como cerrado.
#        if self.start_balance == self.end_balance:
        if self.differance == 0:
            self.state='close'
        else:
            raise Warning(_('Reconcile Balance and Ending Balance is should be same'))
        return True

    
    @api.depends('journal_entry_ids')
    def action_assign(self):     
    
        _document_number = ''
        _move_name = ''
        
        if self.journal_entry_ids:
            
            for journal_entry in self.journal_entry_ids:
                          
                _move_name = journal_entry.payment_id.move_name
                  
                if journal_entry.payment_id.check_number:
                 
                    _document_number = journal_entry.payment_id.check_number                    
                
                elif journal_entry.payment_id.x_transaccion:
                 
                    _document_number = journal_entry.payment_id.x_transaccion
                
                else: 
                    
                    _document_number = journal_entry.move_id.ref
                    _move_name = journal_entry.move_id.name
                    
                journal_entry.write({
                    'document_number': _document_number,
                    'move_name': _move_name
                })
                      
    @api.depends('end_balance')
    def _compute_bank_statement(self):
        
        if self.end_balance:
            self.bank_statement = self.end_balance    
        return True
        
    @api.depends('end_balance','start_balance')
    def _compute_differance(self):
        
        self.differance= int(abs(self.end_balance - self.less_unrepresented_amount - self.deposit_not_credited_bank - self.bank_account))
#        self.differance= abs(self.end_balance - self.start_balance - self.less_unrepresented_amount - self.deposit_not_credited_bank - self.bank_account)
        return True
    
    @api.depends('journal_entry_ids','start_balance')
    def _compute_bank_account(self):
        
        total_debit=0.0
        total_credit=0.0
        if self.journal_entry_ids:
            for journal_entry in self.journal_entry_ids:
                total_debit += journal_entry.debit if journal_entry.currency_id.name != 'USD' else (abs(journal_entry.amount_currency) if journal_entry.credit == 0 else 0)
                total_credit += journal_entry.credit if journal_entry.currency_id.name != 'USD' else (abs(journal_entry.amount_currency) if journal_entry.debit == 0 else 0)
        self.bank_account = (total_debit - total_credit) + self.start_balance
        return True

    @api.depends('journal_entry_ids')
    def _compute_unrepresented_amount(self):
        
        total_credit=0.0
        if self.journal_entry_ids:
            for journal_entry in self.journal_entry_ids:
                if not journal_entry.is_bank_reconcile:
                    total_credit += journal_entry.credit if journal_entry.currency_id.name != 'USD' else (abs(journal_entry.amount_currency) if journal_entry.debit == 0 else 0)
        self.less_unrepresented_amount = total_credit
        return True 
        
    @api.depends('journal_entry_ids')
    def _compute_credited_bank(self):
        
        total_debit=0.0
        if self.journal_entry_ids:
            for journal_entry in self.journal_entry_ids:
                if not journal_entry.is_bank_reconcile:
                    total_debit += journal_entry.debit if journal_entry.currency_id.name != 'USD' else (abs(journal_entry.amount_currency) if journal_entry.credit == 0 else 0)
        self.deposit_not_credited_bank = total_debit
        return True

        
    def button_dummy(self):
        return {
    'type': 'ir.actions.client',
    'tag': 'reload',  }

    def unlink(self):
        for record in self:
            for journal_entry in record.journal_entry_ids:
                if journal_entry.is_bank_reconcile:
                    raise Warning('No es posible eliminar ya que contiene lineas Conciliadas')        
        return super(bank_reconciliation, self).unlink()

    def write(self,vals):
        
        for rec in self:
            antes = []
            if rec.journal_entry_ids:                
                for id in rec.journal_entry_ids:
                    antes.append(id.id)
        
            result = super(bank_reconciliation,self).write(vals)

            despues = []
            for id in rec.journal_entry_ids:
                despues.append(id.id)

            c1 = set(antes)
            c2 = set(despues)
            ids = list(c1-c2)

            for va in self.env['account.move.line'].browse(ids):
                va.is_bank_reconcile = False

        return result        
        

class account_move_line(models.Model):
    
    _inherit = 'account.move.line'
    
    is_bank_reconcile=fields.Boolean(string="IS Reconcile", copy=False)
    is_not_confirm = fields.Boolean(string="Is Not Confirm", copy=False)
    document_number = fields.Char(string='Doumento No.', copy=False)
    move_name = fields.Char(string='Asiento', copy=False)
    
    
    def action_make_confirm(self):
        
        # Marca registro contable como conciliado.
        if self.env.context.get('state') == 'close':
            raise Warning(_('You can not reconcile the line in close state'))
        else:    
            self.is_bank_reconcile=True    
        
        return True
        
    
    def action_cancel_confirm(self):
        
        # Marca registro contable como no conciliado.
        if self.env.context.get('state') == 'close':
            raise Warning(_('You can not un-reconcile the line in close state'))
        else:    
            self.is_bank_reconcile=False    
        
        return True

    @api.depends('move_id.name','ref')
    def _datos_adicionales(self):
        for record in self:
            if record.payment_id.check_number:
                record.document_number = record.payment_id.check_number or ''
            elif record.payment_id.x_transaccion:
                record.document_number = record.payment_id.x_transaccion or ''
            else:
                record.document_number = record.move_id.ref

            record.move_name = record.move_id.name or ''
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: