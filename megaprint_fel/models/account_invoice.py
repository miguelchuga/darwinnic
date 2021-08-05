# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class mpfel_account_invoice(models.Model):
    _name = "account.move"
    _inherit = "account.move"

    def _cacular_gface_fel(self):
        if self.gface_dte_number:
            self.x_documento_gface_fel = 'CAE : '+self.gface_dte_cae
        else:
            if self.mpfel_sat_uuid:
                self.x_documento_gface_fel = 'UUID SAT: '+self.mpfel_sat_uuid
            else:
                self.x_documento_gface_fel = ' '

    serie_gt = fields.Char('Serie de la factura', size=40)
    mpfel_file_name = fields.Char('Nombre del archivo',readonly=True)
    mpfel_pdf = fields.Binary(string='PDF Factura',readonly=True)

    mpfel_serial = fields.Char('Serial Document', copy=False)
    mpfel_number = fields.Char('FEL Number', copy=False)
    date_sign = fields.Char('Fecha y hora emisión', copy=False)

    gface_dte_serial = fields.Char('Serie DTE')
    gface_dte_number = fields.Char('Número DTE')

    mpfel_uuid = fields.Char('Document UUID', copy=False)
    mpfel_sat_uuid = fields.Char('SAT UUID', copy=False)
    mpfel_source_xml = fields.Text('Source XML', copy=False)
    mpfel_signed_xml = fields.Text('Signed XML', copy=False)
    mpfel_result_xml = fields.Text('Result XML', copy=False)
    mpfel_void_uuid = fields.Char('Void document UUID', copy=False)
    mpfel_void_sat_uuid = fields.Char('Void SAT UUID', copy=False)
    mpfel_void_source_xml = fields.Text('Void source XML', copy=False)
    mpfel_void_signed_xml = fields.Text('Void signed XML', copy=False)
    mpfel_void_result_xml = fields.Text('Void result XML', copy=False)
    mpfel_sign_date = fields.Char('Sign date', copy=False)
    invoice_line__fel_ids = fields.One2many('account.invoice.line.fel', 'invoice_id', string='Invoice Lines Fel',
        readonly=True, copy=False)
    x_documento_gface_fel = fields.Text('Gface/Fel', compute=_cacular_gface_fel)
    x_orden  = fields.Char('No. OrdeN', copy=False)

    #EXPORTACION
    x_incoterms_id = fields.Many2one('stock.incoterms', 'Incoterms')
    x_nombreconsignatarioodestinatario = fields.Char('Congnatario', copy=False)
    x_direccionconsignatarioodestinatario = fields.Char('Dirección Congnatario', copy=False)
    x_nombrecomprador = fields.Char('Nombre comprador', copy=False)
    x_direccioncomprador = fields.Char('Dirección comprador', copy=False)

    x_nit_generico = fields.Boolean(string='Es generico ?')

    def post(self):
        if self.type=='out_invoice' or self.type=='out_refund' or self.type =='in_invoice':
            settings = self.env['mpfel.settings'].search([('company_id','=',self.company_id.id)])
            if settings:
                settings.sign_document(self)
            else:
                raise UserError(_('Megaprint FEL settings not found'))
        return super(mpfel_account_invoice, self).post()

    def mpfel_invoice_void(self):
        settings = self.env['mpfel.settings'].search([])
        for inv in self:
            if inv.mpfel_sat_uuid:
                settings.void_document(inv)
        return True



class account_invoice_line_fel(models.Model):
    _name = 'account.invoice.line.fel'



    orden= fields.Integer('Orden')
    bien_servicio= fields.Char('Bien/Servicio')    
    product_id = fields.Many2one('product.product', 'Producto')
    unidad_medida = fields.Char('Unidad medida')    
    descripcion = fields.Char('Descripcion')    
    unit_price  = fields.Float('Precio')
    qty = fields.Float('Cantidad')
    qty_bonif = fields.Float('Bonificación')
    qty_total = fields.Float('Qty total')

    subtotal = fields.Float('Subtotal')
    descuento = fields.Float('Descuento')
    total_mas_descuento = fields.Float('Total')
    total = fields.Float('Total')

    gravable = fields.Char('Gravable')
    txt_iva = fields.Char('Texto iva')
    monto_gravable = fields.Float('Monto gravable')
    monto_impuesto = fields.Float('Monto impuesto')

    invoice_id = fields.Many2one('account.invoice', string='Invoice Reference',
        ondelete='cascade', index=True)


