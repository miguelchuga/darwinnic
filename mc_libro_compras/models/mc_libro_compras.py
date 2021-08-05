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

#version 12.00

class MCLibroCompras(models.Model):
    
    _name = "mc_libro_compras.mc_libro_compras"
    _description = "Libro de compras Guatemala"

    name = fields.Text(string='Descripción', required=True)
    fecha_desde = fields.Date(string='Fecha desde' , required=True)
    fecha_hasta = fields.Date(string='Fecha hasta' , required=True)
    libro_line_ids = fields.One2many('mc_libro_compras.mc_libro_compras_line','libro_id', string=' ')
    libro_total_ids = fields.One2many('mc_libro_compras.mc_libro_compras_total','libro_id', string=' ')  
    libro_top_proveedores_ids = fields.One2many('mc_libro_compras.mc_libro_compras_top_proveedores','libro_id', string=' ')                            
    company_id  = fields.Many2one('res.company', string='Empresa')
    tipo_fecha = fields.Selection([('documento', 'Documento'), ('contable', 'Contable')], 'Tipo fecha ', select=True,required=True)

    def genera_libro(self):

        self.env["mc_libro_compras.mc_libro_compras_line"].search([('libro_id','=',self.id)]).unlink()
        
        # Asfalgua
        valor_negativo_linea = self.env['ir.config_parameter'].search([('key', '=', 'libro_compras_valor_negativo_linea')])
        no_usar_tasa_de_cambio = self.env['ir.config_parameter'].search([('key', '=', 'libro_compras_no_usar_tasa_de_cambio')])
        no_usar_signo_transaccion = self.env['ir.config_parameter'].search([('key', '=', 'libro_compras_no_usar_signo_transaccion')])
        
        sign = 1

        # Se debe agregar este parametro en : Ajustes / tecnico / Parametros del sistema
        # key = vat
        # value = True
        # cuando se usa res.partner el campo VAT  o cuando se usa el campo ref
        vat_id = self.env['ir.config_parameter'].search([('key', '=', 'vat')]).ids[0]
        _usa_vat = self.env['ir.config_parameter'].browse([vat_id])

        # en la version 13.0 name  <> '/' quiere decir una factura que no esta validada antes se tomaba como borrador
        if self.tipo_fecha == 'documento':
            sql = """
            SELECT company_id, id, date_invoice, date,state
              FROM "MC_libro_compras"
             WHERE   company_id = %s AND date_invoice >= %s AND date_invoice <= %s
             """
            self.env.cr.execute(sql, (self.company_id.id,self.fecha_desde,self.fecha_hasta,))
        else:
            sql = """
            SELECT company_id, id, date_invoice, date,state
              FROM "MC_libro_compras"
             WHERE   company_id = %s AND date >= %s AND date <= %s
             """
            self.env.cr.execute(sql, (self.company_id.id,self.fecha_desde,self.fecha_hasta,))

        doc_count = 0
        
        for query_line in self.env.cr.dictfetchall():

            doc_count += 1
            invoice_id = self.env['account.move'].browse([query_line['id']])
            
            if  not no_usar_signo_transaccion:
            
                sign = invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1

            if invoice_id.name:
                _name = invoice_id.name
            else:
                _name = 'Anulado / Borrador'

            #depende los parametros de la empresa ver arriba
            if _usa_vat.value == 'True':
                _nit_dpi = invoice_id.partner_id.vat
            else:
                _nit_dpi = invoice_id.partner_id.ref
            _proveedor = invoice_id.partner_id.name

            _local_bienes_gravados = 0
            _local_bienes_gravados_combustible = 0
            _local_bienes_exentos = 0
            _local_servicios_gravados = 0
            _local_servicios_exentos = 0
            
            _local_bienes_pequenio_contribuyente = 0
            _local_servicios_pequenio_contribuyente = 0            

            _importacion_bienes_gravados = 0
            _importacion_bienes_gravados_total = 0
            
            _importacion_bienes_exentos = 0
            _importacion_bienes_exentos_total = 0
            
            _importacion_servicios_gravados = 0
            _importacion_servicios_exentos = 0
            _activos_fijos = 0

            _idp = 0
            _timbre_prensa = 0
            _tasa_municipal = 0
            _inguat = 0
            _retension_isr = 0
            _retension_iva = 0
            _iva = 0
            _total = 0
#            _currency_id = invoice_id.currency_id.with_context(date=invoice_id.date_invoice)
            
            # Si la moneda de la compra es quetzales. 
            if self.env.user.company_id.currency_id.id == invoice_id.currency_id.id:
                # El valor en otra moneda es 0.
                _otra_moneda = 0
                
            else:
                # El valor en otra moneda es el monto de la factura.
                _otra_moneda = invoice_id.amount_total 

            for l in invoice_id.invoice_line_ids:

                invoice_line_id = self.env['account.move.line'].browse([ l.id ])
#                _currency_id = invoice_id.currency_id.with_context(date=invoice_id.date_invoice)


#                if  no_usar_tasa_de_cambio:
#                    precio_subtotal = round(invoice_line_id.price_subtotal * invoice_id.amount_total_company_signed / invoice_id.amount_total, 2)
#                else:
#                    precio_subtotal = _currency_id.compute(invoice_line_id.price_subtotal, invoice_id.company_id.currency_id)
                precio_subtotal = invoice_line_id.price_subtotal

                _polizas_importacion = True         
                if valor_negativo_linea and invoice_id.serie_gt == 'POLIZA':
                    # Se hace cuando hay una póliza de importación como en Lubisa.
                    # EN LA POLIZA QUE SE INGRESA SE DEBE PONER EN SERIE POLIZA
                    if precio_subtotal < 0:
                        precio_subtotal = 0
                        _polizas_importacion = False
                    
                # Define si el producto es bien o servicio.
                _tipo = 'servicio'
                if invoice_line_id.product_id.type == 'service':
                    if invoice_line_id.product_id.default_code == 'Local-Bienes':
                        _tipo = 'bien'
                    else:
                        _tipo = 'servicio'
                else:
                    _tipo = 'bien'

                _tiene_iva = False
                _es_idp = False
                
                for t in invoice_line_id.tax_ids:
                    tax_id = self.env['account.tax'].browse([ t.id ])
                    
                    if tax_id.tipo_impuesto == 'iva':
                        _tiene_iva = True
                    if tax_id.tipo_impuesto == 'idp':
                        _tipo = 'bien'
                        _es_idp = True
                
                #SE EVALUA EL TIVPO DE VENTA "FPC" PARA PEQUEÑO CONTRIBUYENTE
                if   invoice_id.journal_id.tipo_venta == 'FPC':
                    if invoice_id.journal_id.local == 'Local' and _tipo == 'bien' and _tiene_iva:
                        _local_bienes_pequenio_contribuyente += precio_subtotal
                    #LOCAL BIENES EXENTO.
                    if invoice_id.journal_id.local == 'Local' and _tipo == 'bien' and not _tiene_iva:
                        _local_bienes_pequenio_contribuyente += precio_subtotal
                    #LOCAL SERVICIOS GRAVADO.
                    if invoice_id.journal_id.local == 'Local' and _tipo == 'servicio' and _tiene_iva:
                        _local_servicios_pequenio_contribuyente += precio_subtotal
                    #LOCAL SERVICIOS exentos.
                    if invoice_id.journal_id.local == 'Local' and _tipo == 'servicio' and not _tiene_iva:
                        _local_servicios_pequenio_contribuyente += precio_subtotal
                else:                    
                    #LOCAL.
                    #LOCAL BIENES GRAVADO.
                    if invoice_id.journal_id.local == 'Local' and _tipo == 'bien' and _tiene_iva:
                        if _es_idp:
                            _local_bienes_gravados_combustible += precio_subtotal
                        else:
                            _local_bienes_gravados += precio_subtotal
                    #LOCAL BIENES EXENTO.
                    if invoice_id.journal_id.local == 'Local' and _tipo == 'bien' and not _tiene_iva:
                        _local_bienes_exentos += precio_subtotal
                    #LOCAL SERVICIOS GRAVADO.
                    if invoice_id.journal_id.local == 'Local' and _tipo == 'servicio' and _tiene_iva:
                        _local_servicios_gravados += precio_subtotal
                    #LOCAL SERVICIOS exentos.
                    if invoice_id.journal_id.local == 'Local' and _tipo == 'servicio' and not _tiene_iva:
                        _local_servicios_exentos += precio_subtotal

#                siempre y cuando no sea lubisa va a ser verdadero
                if _polizas_importacion:
                    if invoice_id.journal_id.local == 'Importacion' and _tipo == 'bien' and _tiene_iva:
                        _importacion_bienes_gravados += precio_subtotal
                    #IMPORTACION BIENES EXENTO.
                    if invoice_id.journal_id.local == 'Importacion' and _tipo == 'bien' and not _tiene_iva:
                        _importacion_bienes_exentos += precio_subtotal
                    #IMPORTACION SERVICIOS GRAVADO.
                    if invoice_id.journal_id.local == 'Importacion' and _tipo == 'servicio' and _tiene_iva:
                        _importacion_servicios_gravados += precio_subtotal
                        #IMPORTACION SERVICIOS exentos.
                    if invoice_id.journal_id.local == 'Importacion' and _tipo == 'servicio' and not _tiene_iva:
                        _importacion_servicios_exentos += precio_subtotal

                    # estos campos debieron llamarse _importacion_gravados_total y _importacion_exentos_total
                    _importacion_bienes_gravados_total = (_importacion_bienes_gravados + _importacion_servicios_gravados) 
                    _importacion_bienes_exentos_total = (_importacion_bienes_exentos + _importacion_servicios_exentos)


            # Suma los impuestos.

            for t in invoice_id.line_ids:
                print(t)

#            tax_ids = self.env['account.move.tax'].search([('invoice_id', '=', invoice_id.id)]).ids
            
#           for t in tax_ids:
                
#                tax_id = self.env['account.move.tax'].browse([ t ])
                
#                if  no_usar_tasa_de_cambio:
#                    _monto = round(tax_id.amount * invoice_id.amount_total_company_signed / invoice_id.amount_total, 2)
#                else:
#                    _currency_id = invoice_id.currency_id.with_context(date=invoice_id.date_invoice)
#                    _monto = _currency_id.compute(tax_id.amount, invoice_id.company_id.currency_id)
#                    var_tax_id = tax_id.tax_id.id
                if t.tax_line_id.tipo_impuesto == 'retiva':
                    _retension_iva = _retension_iva + abs(t.price_total)
                if t.tax_line_id.tipo_impuesto == 'retisr':
                   _retension_isr = _retension_isr + abs(t.price_total)
                if t.tax_line_id.tipo_impuesto == 'municipal':
                   _tasa_municipal = _tasa_municipal + abs(t.price_total)
                if t.tax_line_id.tipo_impuesto == 'idp':
                   _idp = _idp + abs(t.price_total)
                if t.tax_line_id.tipo_impuesto == 'prensa':
                   _timbre_prensa = _timbre_prensa + abs(t.price_total)
                if t.tax_line_id.tipo_impuesto == 'inguat':
                   _inguat = _inguat + abs(t.price_total)
                if t.tax_line_id.tipo_impuesto == 'iva':
                   _iva = _iva + t.price_total
#                   if _iva < 1 and tax_id.tax_id.description == 'IVA por Cobrar Especial':
#                        _iva = abs(tax_id.amount) #SE COLOCA EL MONTO ABSOLUTO DEL IVA POR COBRAR ESPECIAL

            if invoice_id.journal_id.tipo_venta == 'FE':
                # precio_subtotal              
                _total = invoice_id.amount_untaxed + _iva
            else:
                _total = invoice_id.amount_total
            #                if  no_usar_tasa_de_cambio:
#                    _total = invoice_id.amount_total
#                else:
#                    _total = _currency_id.compute(invoice_id.amount_total, invoice_id.company_id.currency_id)
                    
#            if _importacion_servicios_gravados > 0:
#                _importacion_bienes_gravados_total = (_importacion_bienes_gravados + _importacion_servicios_gravados)

#            if _importacion_servicios_exentos > 0:
#                _importacion_bienes_exentos_total = (_importacion_bienes_exentos + _importacion_servicios_exentos)

            invoice_line = {'libro_id':self.id,
                'name': _name,
                'invoice_id': invoice_id.id,
                'partner_id': invoice_id.partner_id.id,
                'journal_id': invoice_id.journal_id.id,
                'company_id': invoice_id.company_id.id,
                'correlativo': doc_count,
                'fecha_documento': invoice_id.invoice_date,
                'fecha_contable': invoice_id.date,
                'serie': invoice_id.serie_gt,
                'documento': invoice_id.name,
                'nit_dpi': _nit_dpi,
                'proveedor': _proveedor,
                'docto_odoo': invoice_id.name,
                'establecimiento': invoice_id.journal_id.establecimiento,
                'tipo_transaccion': invoice_id.journal_id.tipo_transaccion,
                'asiste_libro': invoice_id.journal_id.asiste_libro,
                'local_bienes_gravados': _local_bienes_gravados * sign,
                'local_bienes_pequenio_contribuyente': _local_bienes_pequenio_contribuyente * sign,                
                'local_bienes_gravados_combustible': _local_bienes_gravados_combustible * sign,
                'local_bienes_exentos': _local_bienes_exentos * sign,
                'local_servicios_gravados': _local_servicios_gravados * sign,
                'local_servicios_pequenio_contribuyente':_local_servicios_pequenio_contribuyente * sign,                
                'local_servicios_exentos': _local_servicios_exentos * sign,
                'importacion_bienes_gravados': _importacion_bienes_gravados * sign,
                'importacion_bienes_gravados_total': _importacion_bienes_gravados_total * sign,
                'importacion_bienes_exentos': _importacion_bienes_exentos * sign,
                'importacion_bienes_exentos_total': _importacion_bienes_exentos_total * sign,                
                'importacion_servicios_gravados': _importacion_servicios_gravados * sign,
                'importacion_servicios_exentos': _importacion_servicios_exentos * sign,
                'activos_fijos': _activos_fijos * sign,
                'idp': _idp * sign,
                'timbre_prensa': _timbre_prensa * sign,
                'tasa_municipal': _tasa_municipal * sign,
                'inguat': _inguat * sign,
                'retension_isr': _retension_isr * sign,
                'retension_iva': _retension_iva * sign,
                'iva': _iva * sign,
               # 'total': (_total+_retension_iva+_retension_isr) * sign if (invoice_id.journal_id.asiste_libro =='NC') else (_total+(_retension_iva+_retension_isr) * sign), # solicitan que el valor de las Notas de Crédito se muestre en negativo.
                
                 'total': (_total + _retension_iva + _retension_isr) * sign,
                
                'otra_moneda': _otra_moneda * sign,
                'base': (_local_bienes_gravados + _local_bienes_gravados_combustible + _local_servicios_gravados) * sign
            }

            self.env['mc_libro_compras.mc_libro_compras_line'].create(invoice_line)
            
            print (invoice_line)

        # Elimina total.
        sql = """
                DELETE
                  FROM mc_libro_compras_mc_libro_compras_total
                 WHERE libro_id = %s
              """
        
        self.env.cr.execute(sql, (self.id,))
              
        sql = """
                SELECT SUM(local_bienes_gravados) AS local_bienes_gravados, SUM(local_bienes_pequenio_contribuyente) AS local_bienes_pequenio_contribuyente, SUM(local_bienes_gravados_combustible) AS local_bienes_gravados_combustible
                     , SUM(local_bienes_exentos) AS local_bienes_exentos, SUM(local_servicios_gravados) AS local_servicios_gravados, SUM(local_servicios_pequenio_contribuyente) AS local_servicios_pequenio_contribuyente
                     , SUM(local_servicios_exentos) AS local_servicios_exentos, SUM(importacion_bienes_gravados) AS importacion_bienes_gravados, SUM(importacion_bienes_gravados_total) AS importacion_bienes_gravados_total
                     , SUM(importacion_bienes_exentos) AS importacion_bienes_exentos, SUM(importacion_bienes_exentos_total) AS importacion_bienes_exentos_total, SUM(importacion_servicios_gravados) AS importacion_servicios_gravados
                     , SUM(importacion_servicios_exentos) AS importacion_servicios_exentos, SUM(activos_fijos) AS activos_fijos, SUM(idp) AS idp
                     , SUM(timbre_prensa) AS timbre_prensa, SUM(tasa_municipal) AS tasa_municipal, SUM(inguat) AS inguat
                     , SUM(retension_isr) AS retension_isr, SUM(retension_iva) AS retension_iva, SUM(iva) AS iva
                     , SUM(total) AS total, SUM(otra_moneda) AS otra_moneda, SUM(base) AS base
                  FROM mc_libro_compras_mc_libro_compras_line
                 WHERE company_id = %s AND fecha_documento >= %s AND fecha_documento <= %s
                GROUP BY libro_id
              """
        
        self.env.cr.execute(sql, (self.company_id.id,self.fecha_desde,self.fecha_hasta,))

        for query_line in self.env.cr.dictfetchall():
             
            invoice_line = {'libro_id':self.id,
                'local_bienes_gravados': query_line['local_bienes_gravados'],
                'local_bienes_pequenio_contribuyente': query_line['local_bienes_pequenio_contribuyente'],                
                'local_bienes_gravados_combustible': query_line['local_bienes_gravados_combustible'],
                'local_bienes_exentos': query_line['local_bienes_exentos'],
                'local_servicios_gravados': query_line['local_servicios_gravados'],
                'local_servicios_pequenio_contribuyente': query_line['local_servicios_pequenio_contribuyente'],                
                'local_servicios_exentos': query_line['local_servicios_exentos'],
                'importacion_bienes_gravados': query_line['importacion_bienes_gravados'],
                'importacion_bienes_gravados_total': query_line['importacion_bienes_gravados_total'],
                'importacion_bienes_exentos': query_line['importacion_bienes_exentos'],
                'importacion_bienes_exentos_total': query_line['importacion_bienes_exentos_total'],                
                'importacion_servicios_gravados': query_line['importacion_servicios_gravados'],
                'importacion_servicios_exentos': query_line['importacion_servicios_exentos'],
                'activos_fijos': query_line['activos_fijos'],
                'idp': query_line['idp'],
                'timbre_prensa': query_line['timbre_prensa'],
                'tasa_municipal': query_line['tasa_municipal'],
                'inguat': query_line['inguat'],
                'retension_isr': query_line['retension_isr'],
                'retension_iva': query_line['retension_iva'],
                'iva': query_line['iva'],
                'total': query_line['total'],
                'otra_moneda': query_line['otra_moneda'],
                'base': query_line['base']
            }

            self.env['mc_libro_compras.mc_libro_compras_total'].create(invoice_line)
            
            print (invoice_line)
        
        # Elimina top.
        sql = """
                DELETE
                  FROM mc_libro_compras_mc_libro_compras_top_proveedores
                 WHERE libro_id = %s
              """
                
        self.env.cr.execute(sql, (self.id,))

        sql = """
            Select t.company_id,t.libro_id,t.nit_dpi, t.name, t.cantidad, t.total 
                   From (Select company_id,libro_id,nit_dpi, proveedor AS name, count(libro_id) cantidad, sum(base) total From mc_libro_compras_mc_libro_compras_line where asiste_libro <> 'FE' group by company_id,libro_id,nit_dpi, proveedor)t
            Where t.company_id = %s and t.libro_id = %s
            order by t.total DESC LIMIT 10
              """
         
#        if self.tipo_fecha == 'documento':
#            
#            sql = """
#                 SELECT ref AS nit_dpi, rp.name, d.cantidad, d.total
#                   FROM res_partner rp
#                   JOIN (SELECT partner_id, COUNT(*) As cantidad, SUM(base) AS total
#                           FROM mc_libro_compras_mc_libro_compras_line
#                           WHERE company_id = %s AND fecha_documento >= %s AND fecha_documento <= %s
#                            AND asiste_libro <> 'FE'
#                          GROUP BY partner_id) d ON d.partner_id = rp.id
#                 ORDER BY d.total DESC
#                 LIMIT 10
#                """
                
#            self.env.cr.execute(sql, (self.company_id.id,self.fecha_desde,self.fecha_hasta,))
            
#        else:
            
#            sql = """               
#                SELECT ref AS nit_dpi, rp.name, d.cantidad, d.total
#                   FROM res_partner rp
#                   JOIN (SELECT partner_id, COUNT(*) As cantidad, SUM(base) AS total
#                           FROM mc_libro_compras_mc_libro_compras_line
#                           WHERE company_id = %s AND fecha_contable >= %s AND fecha_contable <= %s
#                            AND asiste_libro <> 'FE'
#                          GROUP BY partner_id) d ON d.partner_id = rp.id
#                 ORDER BY d.total DESC
#                 LIMIT 10           
#                """

        
        self.env.cr.execute(sql, (self.company_id.id,self.id))
        
        doc_count = 0
        
        for query_line in self.env.cr.dictfetchall():
             
            doc_count += 1
             
            invoice_line = {'libro_id':self.id,
                'correlativo': doc_count,                            
                'nit_dpi': query_line['nit_dpi'],
                'proveedor': query_line['name'],
                'cantidad': query_line['cantidad'],                
                'base': query_line['total']
            }

            self.env['mc_libro_compras.mc_libro_compras_top_proveedores'].create(invoice_line)
            
            print (invoice_line)
            
class MCLibroComprasLine(models.Model):
    
    _name = "mc_libro_compras.mc_libro_compras_line"
    _description = "Libro de compras Guatemala Line"
    _order = "correlativo desc, fecha_documento desc"

    name = fields.Text(string='Descripción', required=True)
    invoice_id  = fields.Many2one('account.move', string='Factura')
    partner_id  = fields.Many2one('res.partner', string='Empresa')
    journal_id  = fields.Many2one('account.journal', string='Diario')
    company_id  = fields.Many2one('res.company', string='Empresa')

    correlativo = fields.Integer(string='Correlativo')
    fecha_documento = fields.Date(string='Fecha documento')
    fecha_contable = fields.Date(string='Fecha contable')

    serie = fields.Char(string='Serie')
    documento = fields.Char(string='Documento')
    nit_dpi = fields.Char(string='Nit o DPI')
    proveedor = fields.Char(string='Nombre del proveedor')
    docto_odoo = fields.Char(string='Docto. Odoo')
    establecimiento = fields.Char(string='Establecimiento')
    tipo_transaccion = fields.Char(string='Tipo transaccion')
    asiste_libro = fields.Char(string='Asiste libro')

    idp = fields.Float(string='IDP')
    timbre_prensa = fields.Float(string='Timbre prensa')
    tasa_municipal = fields.Float(string='Tasa municipal')
    inguat = fields.Float(string='Inguat')
    retension_isr = fields.Float(string='Retension ISR')
    retension_iva = fields.Float(string='Retension IVA')

    local_bienes_gravados = fields.Float(string='Local bienes gravados')
    local_bienes_gravados_combustible = fields.Float(string='Local bienes gravado combustible')
    local_bienes_exentos = fields.Float(string='Local bienes exentos')
    local_bienes_pequenio_contribuyente = fields.Float(string = 'Local bienes Pequeño Contribuyente')#SE AGREGA CAMPO DE BIEN PARA PEQUEÑO CONTRIBUYENTE
        
    local_servicios_gravados = fields.Float(string='Local servicios gravados')
    local_servicios_exentos = fields.Float(string='Local servicios exentos')
    local_servicios_pequenio_contribuyente = fields.Float(string = 'Local servicios Pequeño Contribuyente')#SE AGREGA CAMPO DE SERVICIO PARA PEQUEÑO CONTRIBUYENTE
    
    importacion_bienes_gravados = fields.Float(string='Importación bienes gravados')
    importacion_bienes_gravados_total = fields.Float(string='TOTAL IMPORTACION GRAVADOS')

    importacion_bienes_exentos = fields.Float(string='Importación bienes exentos')
    importacion_bienes_exentos_total = fields.Float(string='TOTAL IMPORTACIN EXENTOS')

    importacion_servicios_gravados = fields.Float(string='Importación servicios gravados')
    importacion_servicios_exentos = fields.Float(string='Importación servicios exentos')
    activos_fijos = fields.Float(string='Activos fijos')

    iva = fields.Float(string='IVA')
    total = fields.Float(string='Total')
    otra_moneda = fields.Float(string='Valor en otra moneda')
    base = fields.Float(string='Monto base top proveedores')
    
    libro_id = fields.Many2one('mc_libro_compras.mc_libro_compras', string='Compras referencia', ondelete='cascade', index=True)
    
class MCLibroComprasTotal(models.Model):
    
    _name = "mc_libro_compras.mc_libro_compras_total"
    _description = "Libro de compras Guatemala total"

    idp = fields.Float(string='IDP')
    timbre_prensa = fields.Float(string='Timbre prensa')
    tasa_municipal = fields.Float(string='Tasa municipal')
    inguat = fields.Float(string='Inguat')
    retension_isr = fields.Float(string='Retension ISR')
    retension_iva = fields.Float(string='Retension IVA')

    local_bienes_gravados = fields.Float(string='Local bienes gravados')
    local_bienes_gravados_combustible = fields.Float(string='Local bienes gravado combustible')
    local_bienes_exentos = fields.Float(string='Local bienes exentos')
    local_bienes_pequenio_contribuyente = fields.Float(string = 'Local bienes Pequeño Contribuyente')
        
    local_servicios_gravados = fields.Float(string='Local servicios gravados')
    local_servicios_exentos = fields.Float(string='Local servicios exentos')
    local_servicios_pequenio_contribuyente = fields.Float(string = 'Local servicios Pequeño Contribuyente')
    
    importacion_bienes_gravados = fields.Float(string='Importación bienes gravados')
    importacion_bienes_gravados_total = fields.Float(string='Importación bienes gravados total')

    importacion_bienes_exentos = fields.Float(string='Importación bienes exentos')
    importacion_bienes_exentos_total = fields.Float(string='Importación bienes exentos total')

    importacion_servicios_gravados = fields.Float(string='Importación servicios gravados')
    importacion_servicios_exentos = fields.Float(string='Importación servicios exentos')
    activos_fijos = fields.Float(string='Activos fijos')

    iva = fields.Float(string='IVA')
    total = fields.Float(string='Total')
    otra_moneda = fields.Float(string='Valor en otra moneda')
    base = fields.Float(string='Monto base top proveedores')
    
    libro_id = fields.Many2one('mc_libro_compras.mc_libro_compras', string='Compras Total', ondelete='cascade', index=True)
    
class MCLibroComprasTop(models.Model):
    
    _name = "mc_libro_compras.mc_libro_compras_top_proveedores"
    _description = "Libro de compras Guatemala top proveedores"
    _order = "correlativo asc"

    correlativo = fields.Integer(string='Correlativo')  
    nit_dpi = fields.Char(string='Nit o DPI')
    proveedor = fields.Char(string='Nombre del proveedor')
    cantidad = fields.Integer(string='Cantidad')
    base = fields.Float(string='Monto base top proveedores')
    
    libro_id = fields.Many2one('mc_libro_compras.mc_libro_compras', string='Compras referencia', ondelete='cascade', index=True)
    
class PurchaseOrderLine(models.Model):
    
    _inherit = 'account.tax'
    
    tipo_impuesto = fields.Selection([('idp', 'IDP'), ('prensa', 'Timbre prensa'), 
                                      ('municipal', 'Tasa municipal'), ('inguat', 'Inguat'), 
                                      ('retisr', 'Retensión isr'), ('retiva', 'Retensión IVA'),('iva', 'IVA')], 'Tipo impuesto ', select=True)
