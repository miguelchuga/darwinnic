


# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

from odoo.exceptions import UserError

from odoo.exceptions import UserError
from datetime import datetime
import re

from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError



class MCLibroVentas(models.Model):

    _name = "mc_libro_ventas.mc_libro_ventas"
    _description = "Libro de ventas Guatemala"

    name = fields.Text(string='Descripción', required=True)
    fecha_desde = fields.Date(string='Fecha desde' , required=True)
    fecha_hasta = fields.Date(string='Fecha hasta' , required=True)
    libro_line_ids = fields.One2many('mc_libro_ventas.mc_libro_ventas_line','libro_id', string=' ')                            
    company_id  = fields.Many2one('res.company', string='Empresa')
    tipo_fecha = fields.Selection([('documento', 'Documento'), ('contable', 'Contable')], 'Tipo fecha ', select=True,required=True)

    def genera_libro(self):

        self.env["mc_libro_ventas.mc_libro_ventas_line"].search([('libro_id','=',self.id)]).unlink()
        
        if self.tipo_fecha == 'documento':
            sql = """
            SELECT company_id, id, date_invoice, date,state
              FROM "MC_libro_ventas"
             WHERE state <> 'draft' and company_id =  %s and date_invoice >= %s and date_invoice <= %s
             """
            self.env.cr.execute(sql, (self.company_id.id,self.fecha_desde,self.fecha_hasta,))
        else:
            sql = """
            SELECT company_id, id, date_invoice, date,state
              FROM "MC_libro_ventas"
             WHERE state <> 'draft' and company_id =  %s and date >= %s and date <= %s
             """
            self.env.cr.execute(sql, (self.company_id.id,self.fecha_desde,self.fecha_hasta,))

        doc_count = 0
        
        for query_line in self.env.cr.dictfetchall():

            doc_count += 1
            invoice_id = self.env['account.move'].browse([query_line['id']])
#            move_id = self.env['account.move'].browse([invoice_id.move_id.id])
            print ("primera")
            print (invoice_id.id)
            sign = invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
          
            #para NEO
            _neo = self.env['ir.model.fields'].search([ ('name', '=', 'x_es_generico'),('model', '=', 'res.partner') ]).ids
            #cuando ventas tenemos fel         
            _fel = self.env['ir.model.fields'].search([ ('name', '=', 'mpfel_sat_uuid'),('model', '=', 'account.invoice') ]).ids

            if _neo:
                if invoice_id.partner_id.x_es_generico: 
                    _nit_dpi = invoice_id.x_nit_generico
                    _nombre = invoice_id.x_nombre_generico
                else:
                    _nit_dpi = invoice_id.partner_id.ref
                    _nombre = invoice_id.partner_id.name
            else:
                _nit_dpi = invoice_id.partner_id.ref
                _nombre = invoice_id.partner_id.name

            if  _fel:           
                if  invoice_id.mpfel_sat_uuid:
                    _serie = invoice_id.mpfel_serial
                else:                
                    _serie = invoice_id.journal_id.serie_venta
            else:
                    _serie = invoice_id.journal_id.serie_venta
            
            if invoice_id.name:
                if  _fel:
                    if  invoice_id.mpfel_sat_uuid:
                        _name = invoice_id.number
                        _documento = invoice_id.mpfel_number                    
                    else:
                        _name = invoice_id.number
                        _documento = invoice_id.number
                else:
                        _name = invoice_id.name
                        _documento = invoice_id.name
                    
                #_documento = invoice_id.number[14:]
            else:
                                               
                _documento = ''
                _name = 'ANULADA'

            if invoice_id.state == 'cancel':
                
                _estado = 'A'
                _name = 'ANULADA'
                _nombre = 'ANULADA'

                if _fel:                
                    if  invoice_id.mpfel_sat_uuid:
                        _documento = invoice_id.mpfel_number                    
                    else:
                        _documento = invoice_id.name
                else:
                        _documento = invoice_id.name

                #_documento = invoice_id.move_name
                _nit_dpi = ''
                
            else:
                _estado = 'E'

            _local_bienes_gravados = 0
            _local_servicios_gravados = 0
            _local_bienes_exentas = 0
            _local_servicios_exentas = 0

            _exportacion_bienes_gravados = 0
            _exportacion_servicios_gravados = 0
            _exportacion_bienes_exentos = 0
            _exportacion_servicios_exentos = 0

            _local_notas_abono = 0
            _exportacion_notas_abono = 0

            _retension_isr = 0
            _retension_iva = 0
            _iva = 0
            _total = 0
            _otra_moneda = 0
            _tipo_cambio = 1
            
            _descuento_redondeo = 0 
#            _currency_id = invoice_id.currency_id.with_context(date=invoice_id.date_invoice)

            if self.env.user.company_id.currency_id.id != invoice_id.currency_id.id:
                print (invoice_id.id)
                _tipo_cambio = 0.00
                _otra_moneda = 0.00

                if invoice_id.amount_total > 0:
#chequear esto en version 13 para las facturas en otra moneda
                    _tipo_cambio = invoice_id.invoice_id / invoice_id.amount_total
                    _otra_moneda = invoice_id.amount_total

            if invoice_id.state == 'cancel':            
                _otra_moneda = 0.00
                
            else:                
                _total = (invoice_id.amount_total * sign)

#            if invoice_id.journal_id.tipo_venta == 'NC' or invoice_id.journal_id.tipo_venta == 'NA':
#            _total = _total * sign
           
                for l in invoice_id.invoice_line_ids:
                    invoice_line_id = self.env['account.move.line'].browse([ l.id ])
                  
                    # Define si el producto es bien o servicios.
                    _tipo = 'servicio'
                    if invoice_line_id.product_id.type == 'service':
                        if invoice_line_id.product_id.default_code == 'Local-Bienes':
                            _tipo = 'bien'
                        else:
                            _tipo = 'servicio'
                    else:
                        _tipo = 'bien'
    
                    _tiene_iva = False
                    for t in invoice_line_id.tax_ids:
                        tax_id = self.env['account.tax'].browse([t.id])

                        if tax_id.tipo_impuesto == 'iva':
                            _tiene_iva = True
                        if tax_id.tipo_impuesto == 'idp':
                            _tipo = 'bien'
                            _es_idp = True

                    # Este valor ya viene negativo de la factura, si está positivo no es un error de este proceso, se debe hacer un update al documento.
                    precio_subtotal = (invoice_line_id.price_subtotal )
                    
                    # Local.
                    if invoice_id.journal_id.tipo_venta == 'NA' or invoice_id.journal_id.tipo_venta == 'NAE':
                        _local_notas_abono += precio_subtotal   
                    else:
                        if invoice_line_id.product_id.default_code in ('REDONDEO','DESCUENTO'):
                            _descuento_redondeo += precio_subtotal
                        else:
                            if invoice_id.journal_id.local == 'Local' and _tipo == 'bien' and _tiene_iva:
                                _local_bienes_gravados += precio_subtotal
                            if invoice_id.journal_id.local == 'Local' and _tipo == 'bien' and not _tiene_iva:
                                _local_bienes_exentas += precio_subtotal
                            if invoice_id.journal_id.local == 'Local' and _tipo == 'servicio' and _tiene_iva:
                                _local_servicios_gravados += precio_subtotal
                            if invoice_id.journal_id.local == 'Local' and _tipo == 'servicio' and not _tiene_iva:
                                _local_servicios_exentas += precio_subtotal
                            # Exportación.
                            if invoice_id.journal_id.local == 'Exportacion' and _tipo == 'bien' and _tiene_iva:
                                _exportacion_bienes_gravados += precio_subtotal
                            if invoice_id.journal_id.local == 'Exportacion' and _tipo == 'bien' and not _tiene_iva:
                                _exportacion_bienes_exentos += precio_subtotal
                            if invoice_id.journal_id.local == 'Exportacion' and _tipo == 'servicio' and _tiene_iva:
                                _exportacion_servicios_gravados += precio_subtotal
                            if invoice_id.journal_id.local == 'Exportacion' and _tipo == 'servicio' and not _tiene_iva:
                                _exportacion_servicios_exentos += precio_subtotal
    
                # Suma los impuestos.
#                tax_ids = self.env['account.invoice.tax'].search([('invoice_id', '=', invoice_id.id)]).ids
                for t in invoice_id.line_ids:
#                for t in tax_ids:
#                    tax_id = self.env['account.invoice.tax'].browse([ t ])
    
#                    move_tax_ids = self.env['account.move.line'].search([('move_id', '=', invoice_id.move_id.id),('account_id', '=', tax_id.account_id.id)]).ids
#                    for tm in move_tax_ids:
#                        move_tax_id = self.env['account.move.line'].browse([ tm ])
    
                    if t.tax_line_id.tipo_impuesto == 'retiva':
                        _retension_iva = _retension_iva +t.price_total
                    if t.tax_line_id.tipo_impuesto == 'retisr':
                       _retension_isr = _retension_isr + t.price_total
                    if t.tax_line_id.tipo_impuesto == 'iva':
                        if invoice_id.type == 'out_refund':
                            _iva = _iva + (t.price_total * sign)
                        else:
                            _iva = _iva + (t.price_total * sign)

            if _local_bienes_gravados > 0:
                _local_bienes_gravados += _descuento_redondeo
            else:
                _local_servicios_gravados += _descuento_redondeo


            invoice_line = {'libro_id':self.id,
                'correlativo': doc_count,
                'name': _name,
                'invoice_id': invoice_id.id,
                'partner_id': invoice_id.partner_id.id,
                'journal_id': invoice_id.journal_id.id,
                'company_id': invoice_id.company_id.id,
                'fecha_documento': invoice_id.invoice_date,
                'fecha_contable': invoice_id.invoice_date,
                'documento': _documento,
                'nit_dpi': _nit_dpi,
                'nombre': _nombre,
                'establecimiento': invoice_id.journal_id.establecimiento,
                'tipo_documento': invoice_id.journal_id.tipo_venta,
                'asiste_libro': invoice_id.journal_id.asiste_libro,
                'tipo_transaccion': invoice_id.journal_id.tipo_transaccion,
                'serie_venta': _serie,
                'estado': _estado,
                'local_bienes_gravados': _local_bienes_gravados,
                'local_servicios_gravados': _local_servicios_gravados,
                'local_bienes_exentas': _local_bienes_exentas,
                'local_servicios_exentas': _local_servicios_exentas,
                'local_notas_abono':_local_notas_abono,
                'exportacion_bienes_gravados': _exportacion_bienes_gravados,
                'exportacion_servicios_gravados': _exportacion_servicios_gravados,
                'exportacion_bienes_exentos': _exportacion_bienes_exentos,
                'exportacion_servicios_exentos': _exportacion_servicios_exentos,
                'retension_isr': _retension_isr,
                'retension_iva': _retension_iva,
                'iva': _iva,
                'total': (_total-abs(_descuento_redondeo)), # Se aplica la funcion abs() a la variables "descuento_redondeo" ya que ese valor viene negativo
                'otra_moneda': _otra_moneda,
                'tipo_cambio': _tipo_cambio
            }

            self.env['mc_libro_ventas.mc_libro_ventas_line'].create(invoice_line)

class MCLibroVentasLine(models.Model):
    
    _name = "mc_libro_ventas.mc_libro_ventas_line"
    _description = "Libro de ventas Guatemala Line"
    _order = "fecha_documento desc"

    correlativo = fields.Integer(string='Correlativo')
    name = fields.Text(string='Descripción', required=True)
    establecimiento = fields.Char(string='Establecimiento')
    invoice_id  = fields.Many2one('account.move', string='Factura')
    partner_id  = fields.Many2one('res.partner', string='Empresa')
    journal_id  = fields.Many2one('account.journal', string='Diario')
    company_id  = fields.Many2one('res.company', string='Empresa')

    fecha_documento = fields.Date(string='Fecha documento')
    fecha_contable = fields.Date(string='Fecha contable')
    asiste_libro = fields.Char(string='Asiste libro')
    tipo_transaccion = fields.Char(string='Tipo transacción')
    tipo_documento = fields.Char(string='Tipo de documento')
    serie_venta = fields.Char(string='Serie de venta')
    documento = fields.Char(string='No. Documento')
    nit_dpi = fields.Char(string='NIT o DPI')
    nombre = fields.Char(string='Nombre del cliente')

    local_bienes_gravados = fields.Float(string='Local bienes gravados')
    local_servicios_gravados = fields.Float(string='Local servicios gravados')
    local_bienes_exentas = fields.Float(string='Local bienes exentas')
    local_servicios_exentas = fields.Float(string='Local servicios exentas')

    exportacion_bienes_gravados = fields.Float(string='Exportación bienes gravados')
    exportacion_servicios_gravados = fields.Float(string='Exportación servicios gravados')
    exportacion_bienes_exentos = fields.Float(string='Exportación bienes exentos')
    exportacion_servicios_exentos = fields.Float(string='Exportación servicios exentos')

    local_notas_abono = fields.Float(string='Notas de abono local')
    exportacion_notas_abono = fields.Float(string='Notas de Abono exportación')

    retension_isr = fields.Float(string='Retensión ISR')
    retension_iva = fields.Float(string='Retensión IVA')

    iva = fields.Float(string='IVA')
    total = fields.Float(string='Total')
    otra_moneda = fields.Float(string='Valor en otra moneda')
    tipo_cambio = fields.Float(string='Tipo cambio')
    
    libro_id = fields.Many2one('mc_libro_ventas.mc_libro_ventas', string='ventas referencia', ondelete='cascade', index=True)

    estado = fields.Char(string='Estado')
