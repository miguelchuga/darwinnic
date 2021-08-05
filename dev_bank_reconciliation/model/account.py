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

class sale_order(models.Model):
    
    _inherit = "account.account"
    
    account_bool=fields.Boolean(string='Is_Bank')
	
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

class accountPayment(models.Model):
    _inherit = 'account.payment'

    x_transaccion = fields.Char(string='Transaccion')
    x_account_analityc_tag_id = fields.Many2one(comodel_name='account.analytic.tag', string='Etiqueta analítica')
    x_deposito = fields.Char(string='No. deposito')
    x_cheque_manual = fields.Char(string='Cheque manual')
    check_number = fields.Integer(string='Número de cheque')
    
    
    

    
    