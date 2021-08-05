# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd. (<http://devintellecs.com>).
#
##############################################################################
import time
from openerp.report import report_sxw
from openerp.osv import osv
import datetime
#from openerp.tools import amount_to_text_en

class bank_reconcile(report_sxw.rml_parse):

    def get_reconsile_entry(self, o):   
    
        res=[]     
        if o.journal_entry_ids:
            
            for jou_id in o.journal_entry_ids:
                
                if  jou_id.is_bank_reconcile:
                    res.append({
                            'date':jou_id.date or False,
                            'name':jou_id.name or False,
                            'ref':jou_id.ref or False,
                            'credit':jou_id.credit or False,
                            'debit':jou_id.debit or False,
                    })            
            return res        
        return False
    
    def get_unreconsile_entry(self, o):   
        
        res=[]     
        if o.journal_entry_ids:
            for jou_id in o.journal_entry_ids:
                if not jou_id.is_bank_reconcile:
                    res.append({
                            'date':jou_id.date or False,
                            'name':jou_id.name or False,
                            'ref':jou_id.ref or False,
                            'credit':jou_id.credit or False,
                            'debit':jou_id.debit or False,
                    })
            return res
        return False
    
    def get_total_unreconcile(self,o):
        
        total=0.0
        if o.journal_entry_ids:
            for jou_id in o.journal_entry_ids:
                if not jou_id.is_bank_reconcile:
                    total += jou_id.credit
            return total

    def get_total_debit_reconcile(self,o):
        
        total=0.0
        if o.journal_entry_ids:
            for jou_id in o.journal_entry_ids:
                if jou_id.is_bank_reconcile:
                    total += jou_id.debit
            return total
    
    def get_total_credit_reconcile(self,o):
        
        total=0.0
        if o.journal_entry_ids:
            for jou_id in o.journal_entry_ids:
                if jou_id.is_bank_reconcile:
                    total += jou_id.credit                    
            return total        

    def get_total_debit_unreconcile(self,o):
        
        total=0.0
        if o.journal_entry_ids:
            for jou_id in o.journal_entry_ids:
                if not jou_id.is_bank_reconcile:
                    total += jou_id.debit
            return total
        
    def get_total_credit_unreconcile(self,o):
        
        total=0.0
        if o.journal_entry_ids:
            for jou_id in o.journal_entry_ids:
                if not jou_id.is_bank_reconcile:
                    total += jou_id.credit
            return total         

    def __init__(self, cr, uid, name, context):
        
        super(bank_reconcile, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'get_reconsile_entry':self.get_reconsile_entry,
            'get_total_credit_reconcile':self.get_total_credit_reconcile,
            'get_total_debit_reconcile':self.get_total_debit_reconcile,
            'get_total_credit_unreconcile':self.get_total_credit_unreconcile,
            'get_total_debit_unreconcile':self.get_total_debit_unreconcile,
            'get_unreconsile_entry':self.get_unreconsile_entry
        })
    
class report_bank_reconcile(osv.AbstractModel):
    
    _name = 'report.dev_bank_reconciliation.report_bank_reconcile' 
    _inherit = 'report.abstract_report'
    _template = 'dev_bank_reconciliation.report_bank_reconcile'
    _wrapped_report_class = bank_reconcile

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: