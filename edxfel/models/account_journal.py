# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class edxfel_account_journal(models.Model):
    _name = "account.journal"
    _inherit = "account.journal"

    edxfel_type = fields.Selection([
        ('', ''),
        ('FACT', 'FACT'),
        ('FCAM', 'FCAM'),
        ('NCRE', 'NCRE'),
    ], string='FEL Invoice type', default='')
    edxfel_previous_authorization = fields.Char('Previous invoice authorization')
    edxfel_previous_serial = fields.Char('Previous invoice serial')
    edxfel_establishment_code = fields.Char('Establishment code')
    edxfel_establishment_street = fields.Char('Establishment street')
    edxfel_comercial_name = fields.Char('Comercial name')
    edxfel_phone_number = fields.Char('Phone Number')
