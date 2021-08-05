# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class edxfel_account_invoice(models.Model):
    _name = "account.move"
    _inherit = "account.move"


    edxfel_uuid = fields.Char('Document UUID', copy=False)
    edx_serial = fields.Char('Serie DTE')
    edx_number = fields.Char('Número DTE')
    edxfel_sign_date = fields.Datetime('Sign date', copy=False)

    edxfel_signed_xml = fields.Text('Signed XML', copy=False)
    edxfel_void_signed_xml = fields.Text('Signed XML', copy=False)
    edxfel_void_uuid = fields.Char('Void document UUID', copy=False)
    edxfel_void_sat_uuid = fields.Char('Void SAT UUID', copy=False)
    edxfel_void_source_xml = fields.Text('Void source XML', copy=False)



    def action_invoice_open(self):
        settings = self.env['edxfel.settings'].search([])
        if settings:
            settings.sign_document(self)
        else:
            raise UserError(_('edx FEL settings not found'))
        return super(edxfel_account_invoice, self).action_invoice_open()

    def edxfel_invoice_void(self):
        settings = self.env['edxfel.settings'].search([])
        for inv in self:
            if inv.edxfel_sat_uuid:
                settings.void_document(inv)
        return True
