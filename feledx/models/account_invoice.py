# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class edx_account_move(models.Model):
    _name = 'account.move'
    _inherit = 'account.move'

    edxfel_void_source_xml = fields.Text('Void source XML', copy=False,readonly=True,)
    edxfel_void_sat_uuid = fields.Char('Void SAT UUID', copy=False,readonly=True,)
    edxfel_void_uuid = fields.Char('Void document UUID', copy=False,readonly=True,)
    edxfel_void_signed_xml = fields.Text('Signed XML', copy=False,readonly=True,)

    edxfel_source_xml = fields.Text('Signed XML', copy=False,readonly=True,)
    edxfel_signed_xml = fields.Text('Signed XML', copy=False,readonly=True,)
    edxfel_sign_date = fields.Char('Sign date' , copy=False,readonly=True,)
    edx_number = fields.Char('Número DTE' , copy=False,readonly=True,)
    edx_serial = fields.Char('Serie DTE' , copy=False,readonly=True,)
    edxfel_uuid = fields.Char('Document UUID', copy=False,readonly=True,)

    edx_file_name = fields.Char('Nombre del archivo',readonly=True, copy=False)
    edx_pdf = fields.Binary(string='PDF Factura',readonly=True, copy=False)


    def action_post(self):
        settings = self.env['feledx.settings'].search([])
        if settings:
            settings.sign_document(self)
        else:
            raise UserError(_('edx FEL settings not found'))
        return super(edx_account_move, self).action_post()

    def edxfel_invoice_void(self):
        settings = self.env['feledx.settings'].search([])
        for inv in self:
            if inv.edxfel_uuid:
                settings.void_document(inv)
        return True
