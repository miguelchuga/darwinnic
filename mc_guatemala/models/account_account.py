#!/usr/bin/python
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountTax(models.Model):
    _inherit = 'account.tax'
    
    tipo_impuesto = fields.Selection([('idp', 'IDP'), ('prensa', 'Timbre prensa'), 
                                      ('municipal', 'Tasa municipal'), ('inguat', 'Inguat'), 
                                      ('retisr', 'Retensión isr'), ('retiva', 'Retensión IVA'),('iva', 'IVA')], 'Tipo impuesto ')
                                     #, select=True)
    impuesto_total = fields.Boolean('Aplica al total ')