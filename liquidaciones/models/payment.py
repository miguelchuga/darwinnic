# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    liquidaciones_id = fields.Many2one("liquidaciones.liquidaciones", string="Liquidacion", readonly=False, states={'reconciled': [('readonly', True)]}, ondelete='restrict')
    x_account_id = fields.Many2one(comodel_name='account.account', string='Cuenta')
    
