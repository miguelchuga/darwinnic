# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class infilefel_account_journal(models.Model):
    _name = "account.journal"
    _inherit = "account.journal"

    infilefel_type = fields.Selection([
        ('', ''),
        ('FACT', 'FACT'),
        ('FCAM', 'FCAM'),
        ('NCRE', 'NCRE'),
    ], string='FEL Invoice type', default='')
    infilefel_previous_authorization = fields.Char('Previous invoice authorization')
    infilefel_previous_serial = fields.Char('Previous invoice serial')
    infilefel_establishment_code = fields.Char('Establishment code')
    infilefel_establishment_street = fields.Char('Establishment street')
    infilefel_comercial_name = fields.Char('Comercial name')
    infilefel_phone_number = fields.Char('Phone Number')
    ws_url_pdf = fields.Char('PDF document web service URL', default = 'https://')