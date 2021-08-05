# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
#from odoo.exceptions import UserError
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
import requests
import xml.etree.cElementTree as ElementTree
from datetime import datetime
import time
import pytz
import uuid
import xmltodict
import os
import json
import base64
#import pyPdf
import html
from tempfile import gettempdir
from xml.sax.saxutils import unescape


class mpfel_settings(models.Model):
    _name = "mpfel.settings"
    _description = "Megaprint FEL settings"

    ws_url_token = fields.Char('Token web service URL', default = 'https://')
    ws_url_document = fields.Char('Document web service URL', default = 'https://')
    ws_url_void = fields.Char('Void document web service URL', default = 'https://')
    ws_url_pdf = fields.Char('PDF document web service URL', default = 'https://')
    ws_url_signer = fields.Char('Signer web service URL', default = 'https://')
    ws_timeout = fields.Integer('Web service timeout', default=300)
    user = fields.Char('User')
    api_key = fields.Char('API key')
    token = fields.Char('Token')
    token_due_date = fields.Datetime('Token due date')
    megaprint_vat = fields.Char('Megaprint VAT')
    certificate_file = fields.Char('Certificate file')
    path_xml = fields.Char('path xml file')    
    certificate_password = fields.Char('Certificate password')
    signing_type = fields.Selection([
        ('LOCAL', 'Sign documents using local program'),
        ('WS', 'Sign documents using Web Service'),
    ], string='Signing type', default='LOCAL')
    signer_location = fields.Char('Signer program location')
    organization_code = fields.Char('Organization code', default='1')
    vat_affiliation = fields.Selection([
        ('GEN', 'GEN'),
        ('EXE', 'EXE'),
        ('PEQ', 'PEQ'),
    ], string='VAT affiliation', default='GEN')
    isr_scenery = fields.Char('ISR sceneries')
    isr_phrases = fields.Char('ISR phrases')
    excempt_scenery = fields.Char('Excempt scenery')
    company_id = fields.Many2one('res.company', string='Empresa')


    nit_certificador = fields.Char('Nit empresa certificadora')
    nombre_certificador = fields.Char('Nombre empresa certificadora ')
    frase_certificador = fields.Char('Frase empresa o cliente')

    def get_token2(self):
        if self.ws_url_token:
            if self.user:
                if self.api_key:
                    headers = {
                        'Content-Type': 'application/xml',
                    }
                    data = "<SolicitaTokenRequest><usuario>{}</usuario><apikey>{}</apikey></SolicitaTokenRequest>".format(
                        self.user, self.api_key)
                    try:
                        response = requests.post(self.ws_url_token, headers=headers, data=data)
                        if response.ok:
                            text = xmltodict.parse(response.text)
                            token = text['SolicitaTokenResponse']['token']
                            due_date_tag = text['SolicitaTokenResponse']['vigencia']
                            if due_date_tag:
                                token_due_date = datetime.strptime(due_date_tag[0:19],'%Y-%m-%dT%H:%M:%S')#.replace(tzinfo=pytz.timezone(self.env.user.tz))
#                                self.token_due_date = token_due_date
                                _data = {'token':token,
                                         'token_due_date': token_due_date
                                         }
                                self.write(_data)

                    except ValidationError as e:
                        raise ValidationError(_('MPFEL: Error consuming web service: {}').format(e.message))
                else:
                    raise ValidationError(_('MPFEL: API key not set'))
            else:
                raise ValidationError(_('MPFEL: User not set'))
        else:
            raise ValidationError(_('MPFEL: Web service URL for tokens not set'))

    def sign_document(self, invoice):

        def escape_string(value):
            if not value:
                value = ''
            return html.escape(value).encode("ascii", "xmlcharrefreplace").decode('utf8')
#            return value.replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt').replace('"', '&quot;').replace(
#                "'", '&apos;').encode('utf-8')

        _pos_id = self.env['ir.config_parameter'].search([('key', '=', 'pos')]).ids[0]
        _generico_id = self.env['ir.config_parameter'].search([('key', '=', 'generico')]).ids[0]

        _tiene_pos = self.env['ir.config_parameter'].browse([_pos_id])
        _tiene_generico = self.env['ir.config_parameter'].browse([_generico_id])

        token = None
        if not invoice.journal_id.mpfel_type:
            return
        elif invoice.journal_id.mpfel_type == '':
            return
        elif invoice.mpfel_sat_uuid:
            return
        elif not invoice.invoice_date:
            raise UserError(_('Missing document date'))
        elif self.token_due_date:
            if self.token_due_date >= fields.Datetime.now():
                if not invoice.mpfel_uuid:
                    invoice.mpfel_uuid = str(uuid.uuid4()).upper()

                #
                # Líneas del documento
                #
                excempt = False
                excempt_phrase = False
                xml_lines = ''
                taxes = []
                line_number = 0
                for line in invoice.invoice_line_ids:
                    line_number += 1
                    if line.tax_ids:
                        line_gross = round(line.price_unit * line.quantity, 2)
                        line_discount = round(line_gross * line.discount / 100, 2)
                        line_amount = line_gross - line_discount
                    else:
                        line_gross = line.price_subtotal
                        line_discount = round(line_gross * line.discount / 100, 2)
                        line_amount = line_gross - line_discount

                    xml_lines += """<dte:Item BienOServicio="{BienOServicio}" NumeroLinea="{NumeroLinea}">
                            <dte:Cantidad>{Cantidad}</dte:Cantidad>
                            <dte:UnidadMedida>{UnidadMedida}</dte:UnidadMedida>
                            <dte:Descripcion>{Descripcion}</dte:Descripcion>
                            <dte:PrecioUnitario>{PrecioUnitario}</dte:PrecioUnitario>
                            <dte:Precio>{Precio}</dte:Precio>
                            <dte:Descuento>{Descuento}</dte:Descuento>{TituloImpuestos}""".format(
                        BienOServicio='B' if line.product_id.type == 'product' or line.product_id.default_code == 'BIEN' else 'S',
                        NumeroLinea=line_number,
                        Cantidad=line.quantity,
                        UnidadMedida=line.product_uom_id.name[:3],
                        Descripcion=escape_string(line.name),
                        PrecioUnitario=line.price_unit,
                        Precio=line_gross,
                        Descuento=line_discount,
                        TituloImpuestos='' if invoice.journal_id.mpfel_type in ['NABN'] else '<dte:Impuestos>'
                    )
                    line_taxes = 0
                    if invoice.journal_id.mpfel_type not in ['NABN']:
                        for tax_id in line.tax_ids:
                            if tax_id.mpfel_sat_code == 'IVA':
                                amount = 0
                                if invoice.journal_id.mpfel_type not in ['NABN'] and tax_id.amount_type == 'percent':
                                    amount = round(line_amount * tax_id.amount / (100 + tax_id.amount), 2)

                                line_taxes += amount
                                xml_lines += """<dte:Impuesto>
                                        <dte:NombreCorto>{NombreCorto}</dte:NombreCorto>
                                        <dte:CodigoUnidadGravable>{CodigoUnidadGravable}</dte:CodigoUnidadGravable>
                                        <dte:MontoGravable>{MontoGravable}</dte:MontoGravable>
                                        <dte:MontoImpuesto>{MontoImpuesto}</dte:MontoImpuesto>
                                    </dte:Impuesto>
                                """.format(
                                    NombreCorto=tax_id.mpfel_sat_code,
                                    CodigoUnidadGravable='1',
                                    MontoGravable=line.price_subtotal,
                                    MontoImpuesto=amount
                                )
                                tax_added = False
                                for tax_sum in taxes:
                                    if tax_sum['NombreCorto'] == tax_id.mpfel_sat_code:
                                        tax_added = True
                                        tax_sum['Valor'] += amount
                                if not tax_added:
                                    taxes.append({
                                        'NombreCorto': tax_id.mpfel_sat_code,
                                        'Valor': amount
                                    })
                    if invoice.journal_id.mpfel_type not in ['NABN'] and line_taxes == 0:
                        excempt = True
                        xml_lines += """<dte:Impuesto>
                                <dte:NombreCorto>{NombreCorto}</dte:NombreCorto>
                                <dte:CodigoUnidadGravable>{CodigoUnidadGravable}</dte:CodigoUnidadGravable>
                                <dte:MontoGravable>{MontoGravable}</dte:MontoGravable>
                                <dte:MontoImpuesto>{MontoImpuesto}</dte:MontoImpuesto>
                            </dte:Impuesto>
                        """.format(
                            NombreCorto='IVA',
                            CodigoUnidadGravable='2',
                            MontoGravable=line.price_subtotal,
                            MontoImpuesto=0
                        )
                        tax_added = False
                        for tax_sum in taxes:
                            if tax_sum['NombreCorto'] == 'IVA':
                                tax_added = True
                                tax_sum['Valor'] += 0
                        if not tax_added:
                            taxes.append({
                                'NombreCorto': 'IVA',
                                'Valor': 0
                            })

                    xml_lines += """{TituloImpuestos}
                            <dte:Total>{Total}</dte:Total>
                        </dte:Item>
                    """.format(TituloImpuestos='' if invoice.journal_id.mpfel_type in ['NABN'] else '</dte:Impuestos>',
                               Total=line_amount)

                #
                # Frases
                #
                xml_phrases = ''
                if invoice.journal_id.mpfel_type not in ['NCRE', 'NDEB', 'NABN', 'FESP']:
                    xml_phrases = '<dte:Frases>'
                    for scenary in self.isr_scenery.split(','):
                        for phrase in self.isr_phrases.split(','):
                            xml_phrases += '<dte:Frase CodigoEscenario="{CodigoEscenario}" TipoFrase="{TipoFrase}" />'.format(
                                CodigoEscenario=scenary,
                                TipoFrase=phrase
                            )
                    if excempt and not excempt_phrase:
                        xml_phrases += '<dte:Frase CodigoEscenario="{CodigoEscenario}" TipoFrase="{TipoFrase}" />'.format(
                            CodigoEscenario=self.excempt_scenery,
                            TipoFrase='4'
                        )
                        excempt_phrase = True
                    xml_phrases += '</dte:Frases>'
                if xml_phrases == '<dte:Frases></dte:Frases>':
                    xml_phrases = ''

                #                date_sign = invoice.date_invoice+'T'+time.strftime("%H:%M:%S")+'-06:00'
                #
                # Encabezado del documento
                #
                sign_date = datetime.now().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone(self.env.user.tz))
                sign_date_utc = datetime.now().replace(tzinfo=pytz.UTC)
                current_date = sign_date.strftime('%Y-%m-%dT%H:%M:%S-06:00')
                current_time = sign_date.strftime('T%H:%M:%S-06:00')
                invoice_sign_date = str(invoice.invoice_date) + current_time
                date_sign = invoice_sign_date

                if invoice.journal_id.mpfel_type == 'FESP':
                    # Factura especial
                    _NITReceptor = invoice.partner_id.x_dpi if invoice.partner_id.x_dpi else invoice.partner_id.ref.replace(
                        '-', '') or invoice.partner_id.ref.replace('-', '') if invoice.partner_id.ref.replace('-',
                                                                                                              '') else 'CF'
                else:
                    if _tiene_generico.value == 'True':
                        # account.invoice (nombre, nit, direccion)
                        _NombreReceptor = escape_string(invoice.partner_id.name) if not invoice.nombre else invoice.nombre
                        if not invoice.nombre:
                            _NITReceptor = invoice.partner_id.vat.replace('-', '') if invoice.partner_id.vat else 'CF'
                        else:
                            _NITReceptor = invoice.nit
                        _DireccionReceptor = invoice.partner_id.street if not invoice.nombre else invoice.direccion
                    else:
                        _NombreReceptor = escape_string(invoice.partner_id.name)
                        _DireccionReceptor= escape_string((invoice.partner_id.street if invoice.partner_id.street else '') + (' ' + invoice.partner_id.street2 if invoice.partner_id.street2 else '')),
                        _NITReceptor = invoice.partner_id.vat.replace('-', '') if invoice.partner_id.vat else 'CF'



                exportacion = """ Exp="SI" """
                xml = """<?xml version="1.0" encoding="UTF-8"?><dte:GTDocumento Version="0.1" xmlns:dte="http://www.sat.gob.gt/dte/fel/0.2.0" xmlns:xd="http://www.w3.org/2000/09/xmldsig#">
                <dte:SAT ClaseDocumento="dte">
                    <dte:DTE ID="DatosCertificados">
                        <dte:DatosEmision ID="DatosEmision">
                            <dte:DatosGenerales CodigoMoneda="{CodigoMoneda}" {EXP} FechaHoraEmision="{FechaHoraEmision}" {NumeroAcceso} Tipo="{Tipo}"/>
                            <dte:Emisor AfiliacionIVA="{AfiliacionIVA}" CodigoEstablecimiento="{CodigoEstablecimiento}" CorreoEmisor="{CorreoEmisor}" NITEmisor="{NITEmisor}" NombreComercial="{NombreComercial}" NombreEmisor="{NombreEmisor}">
                                <dte:DireccionEmisor>
                                    <dte:Direccion>{DireccionEmisor}</dte:Direccion>
                                    <dte:CodigoPostal>{CodigoPostalEmisor}</dte:CodigoPostal>
                                    <dte:Municipio>{MunicipioEmisor}</dte:Municipio>
                                    <dte:Departamento>{DepartamentoEmisor}</dte:Departamento>
                                    <dte:Pais>{PaisEmisor}</dte:Pais>
                                </dte:DireccionEmisor>
                            </dte:Emisor>
                            <dte:Receptor CorreoReceptor="{CorreoReceptor}" IDReceptor="{NITReceptor}" NombreReceptor="{NombreReceptor}" {_TipoEspecial} >
                                <dte:DireccionReceptor>
                                    <dte:Direccion>{DireccionReceptor}</dte:Direccion>
                                    <dte:CodigoPostal>{CodigoPostal}</dte:CodigoPostal>
                                    <dte:Municipio>{Municipio}</dte:Municipio>
                                    <dte:Departamento>{Departamento}</dte:Departamento>
                                    <dte:Pais>{Pais}</dte:Pais>
                                </dte:DireccionReceptor>
                            </dte:Receptor>
                            {Frases}
                            <dte:Items>
                                {Items}
                            </dte:Items>
                            <dte:Totales>
                                {TituloImpuestos}""".format(
                    CodigoMoneda=invoice.currency_id.name,
                    EXP=exportacion if invoice.journal_id.mpfel_exportacion else '',  # Para exportaciones: 'EXP="SI"'
                    FechaHoraEmision=invoice_sign_date,
                    NumeroAcceso='',
                    Tipo=invoice.journal_id.mpfel_type,
                    AfiliacionIVA=self.vat_affiliation,
                    CodigoEstablecimiento=self.organization_code,
                    CorreoEmisor=invoice.company_id.email if invoice.company_id.email else '',
                    NITEmisor=invoice.company_id.vat.replace('-', '') if invoice.company_id.vat else 'C/F',
                    NombreComercial=escape_string(invoice.company_id.name),
                    NombreEmisor=escape_string(invoice.company_id.name),
                    DireccionEmisor=escape_string((invoice.company_id.street if invoice.company_id.street else '') + (
                        ' ' + invoice.company_id.street2 if invoice.company_id.street2 else '')),
                    CodigoPostalEmisor=invoice.company_id.zip if invoice.company_id.zip else '01001',
                    MunicipioEmisor=escape_string(invoice.company_id.city if invoice.company_id.city else ''),
                    DepartamentoEmisor=escape_string(
                        invoice.company_id.state_id.name if invoice.company_id.state_id else ''),
                    PaisEmisor=invoice.company_id.country_id.code if invoice.company_id.country_id else '',
                    DireccionReceptor=_DireccionReceptor,
                    CorreoReceptor=invoice.partner_id.email if invoice.partner_id.email else '',

                    NITReceptor=_NITReceptor,

                    NombreReceptor=_NombreReceptor,#escape_string(invoice.partner_id.name),
                    _TipoEspecial='TipoEspecial="CUI" ' if invoice.journal_id.mpfel_type == 'FESP' else '',

                    CodigoPostal=invoice.partner_id.zip if invoice.partner_id.zip else '01001',
                    Municipio=escape_string(invoice.partner_id.city) if invoice.partner_id.city else '',
                    Departamento=escape_string(invoice.partner_id.state_id.name) if invoice.partner_id.state_id else '',
                    Pais=invoice.partner_id.country_id.code if invoice.partner_id.country_id else '',
                    Frases=xml_phrases,
                    Items=xml_lines,
                    TituloImpuestos='' if invoice.journal_id.mpfel_type in ['NABN'] else '<dte:TotalImpuestos>'
                )

                if not invoice.journal_id.mpfel_type in ['NABN']:
                    for tax in taxes:
                        xml += '<dte:TotalImpuesto NombreCorto="{NombreCorto}" TotalMontoImpuesto="{TotalMontoImpuesto}"/>'.format(
                            NombreCorto=tax['NombreCorto'],
                            TotalMontoImpuesto=tax['Valor']
                        )

                extras = ''

                if invoice.journal_id.mpfel_type == 'FCAM' and not invoice.journal_id.mpfel_exportacion:
                    # <dte:AbonosFacturaCambiaria Version="1">
                    extras = """
                                <dte:Complementos>
                                    <dte:Complemento IDComplemento="AbonosFacturaCambiaria" NombreComplemento="AbonosFacturaCambiaria" URIComplemento="http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0">
                                        <cfc:AbonosFacturaCambiaria xmlns:cfc="http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0" Version="1">
                                            <cfc:Abono>
                                                <cfc:NumeroAbono>1</cfc:NumeroAbono>
                                                <cfc:FechaVencimiento>{FechaVencimiento}</cfc:FechaVencimiento>
                                                <cfc:MontoAbono>{Monto}</cfc:MontoAbono>
                                            </cfc:Abono>
                                        </cfc:AbonosFacturaCambiaria>
                                    </dte:Complemento>
                                </dte:Complementos>""".format(FechaVencimiento=invoice.invoice_date_due,
                                                              Monto=invoice.amount_total)

                elif invoice.journal_id.mpfel_type == 'FCAM' and invoice.journal_id.mpfel_exportacion:
                    extras = """
                                <dte:Complementos>
                                    <dte:Complemento IDComplemento="1" NombreComplemento="EXPORTACION" URIComplemento="http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0">
                                        <cex:Exportacion xmlns:cex="http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0" Version="1">
                                            <cex:NombreConsignatarioODestinatario>{x_nombreconsignatarioodestinatario}</cex:NombreConsignatarioODestinatario>
                                            <cex:DireccionConsignatarioODestinatario>{x_direccionconsignatarioodestinatario}</cex:DireccionConsignatarioODestinatario>
                                            <cex:NombreComprador>{x_nombrecomprador}</cex:NombreComprador>
                                            <cex:DireccionComprador>{x_direccioncomprador}</cex:DireccionComprador>
                                            <cex:INCOTERM>{x_incoterms_id}</cex:INCOTERM>
                                        </cex:Exportacion>
                                    </dte:Complemento>
                                </dte:Complementos>""".format(
                        x_nombreconsignatarioodestinatario=invoice.x_nombreconsignatarioodestinatario,
                        x_direccionconsignatarioodestinatario=invoice.x_direccionconsignatarioodestinatario,
                        x_nombrecomprador=invoice.x_nombrecomprador, x_direccioncomprador=invoice.x_direccioncomprador,
                        x_incoterms_id=invoice.x_incoterms_id.code)

                elif invoice.journal_id.mpfel_type in ['FESP']:
                    _iva_especial = 0
                    _isr_especial = 0
                    for _tax in invoice.tax_line_ids:
                        if _tax.tax_id.mpfel_sat_code == 'IVA':
                            _iva_especial = _tax.amount
                        if _tax.tax_id.mpfel_sat_code == 'ISR':
                            _isr_especial = abs(_tax.amount)

                    extras = """
                                <dte:Complementos>
                                    <dte:Complemento IDComplemento="1" NombreComplemento="RETENCION" URIComplemento="http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0">
                                        <cfe:RetencionesFacturaEspecial xmlns:cfe="http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0" Version="1">
                                            <cfe:RetencionISR>{ISRespecial}</cfe:RetencionISR>
                                            <cfe:RetencionIVA>{IVAespecial}</cfe:RetencionIVA>
                                            <cfe:TotalMenosRetenciones>{TOTALespecial}</cfe:TotalMenosRetenciones>
                                        </cfe:RetencionesFacturaEspecial>
                                    </dte:Complemento>    
                                </dte:Complementos>""".format(ISRespecial=_isr_especial, IVAespecial=_iva_especial,
                                                              TOTALespecial=invoice.amount_total)
                elif invoice.journal_id.mpfel_type in ['NCRE', 'NDEB']:
                    extras = """
                                <dte:Complementos>
                                    <dte:Complemento IDComplemento="{IDComplemento}" NombreComplemento="{NombreComplemento}" URIComplemento="http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0">
                                        {Referencias}
                                    </dte:Complemento>
                                </dte:Complementos>"""
                    references = """<cno:ReferenciasNota xmlns:cno="http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0"
                                            Version="1" {RegimenAnterior}
                                            NumeroAutorizacionDocumentoOrigen="{DocumentoOrigen}"
                                            FechaEmisionDocumentoOrigen="{FechaEmision}" {MotivoAjuste}
                                        />
                    """
                    id_complemento = ''
                    nombre_complemento = ''
                    if invoice.reversed_entry_id:
                        previous_regime = ''
                        original_document = invoice.reversed_entry_id.ref
                        reason = ''
                        if invoice.reversed_entry_id.mpfel_sat_uuid:
                            id_complemento = 'ReferenciasNota'
                            nombre_complemento = 'ReferenciasNota'
                            original_document = invoice.reversed_entry_id.mpfel_sat_uuid
                            reason = 'MotivoAjuste="{}"'.format(invoice.ref)

                        else:
                            id_complemento = 'ComplementoReferenciaNota'
                            nombre_complemento = 'Complemento Referencia Nota'
                            previous_regime = 'RegimenAntiguo="Antiguo"'
                            original_document = invoice.refund_invoice_id.resolution_id.name
                            reason = 'SerieDocumentoOrigen="{}" NumeroDocumentoOrigen="{}"'.format(
                                invoice.refund_invoice_id.gface_dte_serial[8:9],
                                str(int(invoice.refund_invoice_id.gface_dte_number[16:100])))

                        references = references.format(
                            RegimenAnterior=previous_regime,
                            DocumentoOrigen=original_document,
                            FechaEmision=invoice.reversed_entry_id.invoice_date,
                            MotivoAjuste=reason,
                        )
                    else:
                        id_complemento = 'ComplementoReferenciaNota'
                        nombre_complemento = 'Complemento Referencia Nota'
                        reason = 'SerieDocumentoOrigen="{}" NumeroDocumentoOrigen="{}"'.format(
                            invoice.refund_invoice_id.gface_dte_serial, invoice.refund_invoice_id.resolution_id.name)
                        references = references.format(
                            RegimenAnterior='RegimenAntiguo="Antiguo"',
                            DocumentoOrigen=invoice.journal_id.mpfel_previous_authorization,
                            FechaEmision=invoice.date_invoice,
                            MotivoAjuste=reason,
                        )
                    extras = extras.format(
                        IDComplemento=id_complemento,
                        NombreComplemento=nombre_complemento,
                        Referencias=references
                    )

                # PARA GENERAR EL PDF NECESITA LOS DATOS EXTRAS EN ADENDAS
                if not invoice.journal_id.ws_url_pdf:
                    adendas = ''
                    adendasitem = ''
                else:
                    adendas = """<dte:Adenda>
	   		    <dte:AdendaDetail id="AdendaSummary">
				    <dte:AdendaSummary>
					    <dte:Valor1>{NoPedido}</dte:Valor1>
                        <dte:Valor2>{OrdenCompra}</dte:Valor2>
                        <dte:Valor3>{Vendedor}</dte:Valor3>
				    </dte:AdendaSummary>
  			    <dte:AdendaItems>
                """.format(NoPedido=invoice.origin, OrdenCompra=invoice.x_orden, Vendedor=invoice.user_id.name)

                    adendasitem = ''
                    line_number = 0
                    for line in invoice.invoice_line_ids:
                        line_number += 1
                        line_str = str(line_number)
                        item = line.product_id.default_code
                        adendasitem += """
		   		        <dte:AdendaItem LineaReferencia="{Line_str}">
					        <dte:Valor1>{Item}</dte:Valor1>
				        </dte:AdendaItem>
                        """.format(Line_str=line_str, Line_strA=line_str, Line_strB=line_str, Item=item)

                    adendasitem += """</dte:AdendaItems>
		                </dte:AdendaDetail>
		            </dte:Adenda>
                    """

                xml += """{TituloImpuestos}
                                <dte:GranTotal>{GranTotal}</dte:GranTotal>
                                </dte:Totales>{Complementos}
                            </dte:DatosEmision>
                        </dte:DTE>  
                            {adendas}
                            {adendasitem}
                    </dte:SAT>
                  </dte:GTDocumento>""".format(
                    TituloImpuestos='' if invoice.journal_id.mpfel_type in ['NABN'] else '</dte:TotalImpuestos>',
                    GranTotal=line_amount if invoice.journal_id.mpfel_type in ['FESP'] else invoice.amount_total,
                    Complementos=extras, adendas=adendas, adendasitem=adendasitem)

                source_xml = xml
                print(xml)
                tmp_dir = self.path_xml
                error_message = ''

                sign_document = False
                if self.signing_type == 'LOCAL':
                    source_xml_file = os.path.join(tmp_dir, '{}_source.xml'.format(invoice.mpfel_uuid))
                    signed_xml_file = os.path.join(tmp_dir, '{}.xml'.format(invoice.mpfel_uuid))
                    with open(source_xml_file, 'w') as xml_file:
                        xml_file.write(xml)
                    os.system("java -jar {} {} {} '{}' {} {} {}".format(self.signer_location, source_xml_file,
                                                                        self.certificate_file,
                                                                        self.certificate_password, invoice.mpfel_uuid,
                                                                        tmp_dir, 'DatosEmision'))

                    if os.path.isfile(signed_xml_file):
                        with open(signed_xml_file, 'r') as myfile:
                            xml = myfile.read()
                        sign_document = True
                    else:
                        raise UserError(_('MPFEL: Signed XML file not found'))
                else:

                    headers = {
                        'Content-Type': 'application/xml',

                        'Authorization': 'Bearer {}'.format(self.token)
                    }
                    data = """<?xml version="1.0" encoding="UTF-8" ?>
                                   <FirmaDocumentoRequest id="{}">
                                   <xml_dte><![CDATA[{}]]></xml_dte>
                                </FirmaDocumentoRequest>
                            """.format(invoice.mpfel_uuid, source_xml)
                    response = requests.post(self.ws_url_signer, data=data, headers=headers)
                    result = xmltodict.parse(response.text)
                    xml2 = unescape(response.text).encode('utf-8')
                    xml3 = response.text.replace('&lt;','<')
                    xml3 = xml3.replace('&gt;','>')
                    xml2 = xml3
                    pos = str(xml3).find('<dte:GTDocumento')
                    if pos >= 0:
                        end = str(xml2).find('</dte:GTDocumento>', pos)
                        doc = unescape(str(xml2)[pos:end + 18])

                    if not response.ok:
                        error_message = u''
                        error_message += '\n{}'.format(xml2)
                        raise ValidationError(_(error_message))

                if response.ok:
                    if self.token:
                        headers = {
                            'Content-Type': 'application/xml',
                            'Authorization': 'Bearer {}'.format(self.token)
                        }
                        data = '<?xml version="1.0" encoding="UTF-8" standalone="no"?> <RegistraDocumentoXMLRequest id="{}"><xml_dte><![CDATA[{}]]></xml_dte></RegistraDocumentoXMLRequest>'.format(
                            invoice.mpfel_uuid, doc)

                        try:
                            response = requests.post(self.ws_url_document, headers=headers, data=data)
                            final = unescape(response.text)
                            if response.ok:
                                pos = final.find('<listado_errores>')
                                errores = []
                                if pos >= 0:
                                    end = final.find('</listado_errores>', pos)
                                    errores = unescape(final[pos:end + 18])
                                    errores_dic = xmltodict.parse(errores)

                                if not errores:
                                    pos = final.find('<dte:GTDocumento')
                                    if pos >= 0:
                                        end = final.find('</dte:GTDocumento>', pos)
                                        doc = unescape(final[pos:end + 18])
                                    doc_dic = xmltodict.parse(doc)

                                if errores:
                                    error_message = u''
                                    error_message += '\n{}'.format(errores)

                                    raise UserError(error_message)

                                if not errores:

                                    _mpfel_serial = ''
                                    _mpfel_number = ''
                                    _sat_uuid = str(
                                        doc_dic[u'dte:GTDocumento'][u'dte:SAT'][u'dte:DTE'][u'dte:Certificacion'][
                                            u'dte:NumeroAutorizacion']['#text']).split('-')
                                    _count = 0
                                    for a in _sat_uuid:
                                        if _count == 0:
                                            _mpfel_serial = a
                                        if _count == 1 or _count == 2:
                                            _mpfel_number += a
                                        _count += 1

                                    print(xml)
                                    if invoice.journal_id.ws_url_pdf:
                                        pdf_headers = {
                                            'Content-Type': 'application/xml',
                                            'Authorization': 'Bearer {}'.format(self.token)
                                        }
                                        _sat_uid = str(
                                            doc_dic[u'dte:GTDocumento'][u'dte:SAT'][u'dte:DTE'][u'dte:Certificacion'][
                                                u'dte:NumeroAutorizacion']['#text'])
                                        pdf_data = """<RetornaPDFRequest>                                                    
                                                   <uuid>{ThisisaUUID}</uuid>
                                                </RetornaPDFRequest>
                                              """.format(
                                            ThisisaUUID=_sat_uid
                                        )
                                        pdf_response = requests.post(url=invoice.journal_id.ws_url_pdf,
                                                                     headers=pdf_headers, data=pdf_data)
                                        result_pdf = xmltodict.parse(pdf_response.text)
                                        _pdf = result_pdf['RetornaPDFResponse']['pdf']

                                    if invoice.journal_id.tipo_venta == 'ND':
                                        _data = {
                                            'mpfel_pdf': _pdf if invoice.journal_id.ws_url_pdf else '',
                                            'mpfel_file_name': _sat_uid + '.' + 'pdf' if invoice.journal_id.ws_url_pdf else '',
                                            'type': 'out_invoice',
                                            'amount_total_company_signed': invoice.amount_total_company_signed * -1,
                                            'residual_company_signed': invoice.residual_company_signed * -1,
                                            'amount_total_signed': invoice.amount_total_signed * -1,
                                            'residual_signed': invoice.residual_signed * -1,
                                            'amount_untaxed_signed': invoice.amount_untaxed_signed * -1,
                                            'mpfel_sign_date': invoice_sign_date,
                                            'mpfel_sat_uuid': str(doc_dic[u'dte:GTDocumento'][u'dte:SAT'][u'dte:DTE'][
                                                                      u'dte:Certificacion'][u'dte:NumeroAutorizacion'][
                                                                      '#text']),
                                            'mpfel_source_xml': source_xml,
                                            'mpfel_signed_xml': doc,
                                            'mpfel_result_xml': final,
                                            'mpfel_serial': _mpfel_serial,
                                            'mpfel_number': str(int(_mpfel_number, 16)),
                                            'name': _mpfel_serial + '-' + str(int(_mpfel_number, 16)),
                                            #'move_name': _mpfel_serial + '-' + str(int(_mpfel_number, 16)),
                                            'date_sign': doc_dic[u'dte:GTDocumento'][u'dte:SAT'][u'dte:DTE'][
                                                u'dte:Certificacion'][u'dte:FechaHoraCertificacion']  # date_sign,
                                        }
                                    else:
                                        _data = {
                                            'mpfel_pdf': _pdf if invoice.journal_id.ws_url_pdf else '',
                                            'mpfel_file_name': _sat_uid + '.' + 'pdf' if invoice.journal_id.ws_url_pdf else '',
                                            'mpfel_sat_uuid': str(doc_dic[u'dte:GTDocumento'][u'dte:SAT'][u'dte:DTE'][
                                                                      u'dte:Certificacion'][u'dte:NumeroAutorizacion'][
                                                                      '#text']),
                                            'mpfel_source_xml': source_xml,
                                            'mpfel_signed_xml': doc,
                                            'mpfel_result_xml': final,
                                            'mpfel_serial': _mpfel_serial,
                                            'serie_gt':_mpfel_serial,
                                            'ref':_mpfel_serial + '-' + str(int(_mpfel_number, 16)),
                                            'mpfel_number': str(int(_mpfel_number, 16)),
                                            'name': _mpfel_serial + '-' + str(int(_mpfel_number, 16)),
                                            #'move_name': _mpfel_serial + '-' + str(int(_mpfel_number, 16)),
                                            'date_sign': doc_dic[u'dte:GTDocumento'][u'dte:SAT'][u'dte:DTE'][
                                                u'dte:DatosEmision'][u'dte:DatosGenerales'][u'@FechaHoraEmision'],
                                            # date_sign,
                                            'mpfel_sign_date': doc_dic[u'dte:GTDocumento'][u'dte:SAT'][u'dte:DTE'][
                                               u'dte:Certificacion'][u'dte:FechaHoraCertificacion']
                                            # invoice_sign_date,
                                        }

                                    invoice.write(_data)
                                    _pos_id = self.env['ir.config_parameter'].search([('key', '=', 'pos')]).ids[0]
                                    _generico_id = self.env['ir.config_parameter'].search([('key', '=', 'generico')]).ids[0]

                                    _tiene_pos = self.env['ir.config_parameter'].browse([_pos_id])
                                    _tiene_generico = self.env['ir.config_parameter'].browse([_generico_id])

                                    if _tiene_pos.value == 'True':
                                        _order_id_ = self.env['pos.order'].search([('account_move', '=', invoice.id)])
                                        if _order_id_:
                                            _pos_order_id = self.env['pos.order'].browse([_order_id_.id])
                                            _infilefel_comercial_name = invoice.journal_id.infilefel_comercial_name
                                            _serie_venta = _mpfel_serial
                                            _infilefel_establishment_street = invoice.journal_id.infilefel_establishment_street
                                            _infile_number = str(int(_mpfel_number, 16))
                                            _infilefel_sat_uuid = str(doc_dic[u'dte:GTDocumento'][u'dte:SAT'][u'dte:DTE'][
                                                                      u'dte:Certificacion'][u'dte:NumeroAutorizacion'][
                                                                      '#text'])
                                            _infilefel_sign_date = doc_dic[u'dte:GTDocumento'][u'dte:SAT'][u'dte:DTE'][
                                                u'dte:DatosEmision'][u'dte:DatosGenerales'][u'@FechaHoraEmision']
                                            _nit_empresa = invoice.company_id.vat
                                            _nombre_empresa = invoice.company_id.name

                                            if _tiene_generico.value == 'True':
                                                #account.invoice (nombre, nit, direccion)
                                                _nombre_cliente = invoice.partner_id.name if not _order_id_.nombre else _order_id_.nombre
                                                _nit = invoice.partner_id.vat if not _order_id_.nombre else _order_id_.nit
                                                _direccion_cliente = invoice.partner_id.street if not _order_id_.nombre else _order_id_.direccion
                                            else:
                                                _nombre_cliente = invoice.partner_id.name
                                                _nit = invoice.partner_id.vat
                                                _direccion_cliente = invoice.partner_id.street

                                            _fecha_factura = invoice.invoice_date
                                            _forma_pago = _forma_pago = _pos_order_id.payment_ids[0].payment_method_id.name

                                            _caja = _pos_order_id.config_id.name
                                            _vendedor = _pos_order_id.create_uid.name
                                            _nit_certificador = self.nit_certificador
                                            _nombre_certificador = self.nombre_certificador
                                            _frase_certificador = self.frase_certificador
                                            _pos_order_id.write({'frase_certificador': _frase_certificador,
                                                         'nombre_certificador': _nombre_certificador,
                                                         'nit_certificador': _nit_certificador, 'vendedor': _vendedor,
                                                         'caja': _caja, 'forma_pago': _forma_pago,
                                                         'fecha_factura': _fecha_factura,
                                                         'direccion_cliente': _direccion_cliente, 'nit': _nit,
                                                         'nombre_cliente': _nombre_cliente,
                                                         'infilefel_sat_uuid': _infilefel_sat_uuid,
                                                         'infilefel_sign_date': _infilefel_sign_date,
                                                         'infile_number': _infile_number,
                                                         'nombre_empresa': _nombre_empresa, 'nit_empresa': _nit_empresa,
                                                         'infilefel_comercial_name': _infilefel_comercial_name,
                                                         'serie_venta': _serie_venta,
                                                         'infilefel_establishment_street': _infilefel_establishment_street})

                                        print('miguel')
                            else:
                                raise ValidationError(
                                    _('MPFEL: Response error consuming web service: {}').format(str(response.text)))
                        except ValidationError as e:
                            if len(error_message) <= 2:
                                error_message = ''
                            if hasattr(e, 'object'):
                                if hasattr(e, 'reason'):
                                    error_message += u"{}: {}".format(e.reason, e.object)
                                else:
                                    error_message += u" {}".format(e.object)
                            elif hasattr(e, 'message'):
                                error_message += e.message
                            elif hasattr(e, 'name'):
                                error_message += e.name
                            else:
                                error_message += e
                            raise ValidationError(_('MPFEL: Error consuming web service: {}').format(error_message))
                    else:
                        raise ValidationError(_('MPFEL: API key not set'))
                else:
                    raise ValidationError(_('MPFEL Signer: {}').format(result['message']))
            else:
                raise ValidationError(_('MPFEL: Token expired'))
        else:
            raise ValidationError(_('MPFEL: Token not set'))

    def void_document(self, invoice):

        def escape_string(value):
            return value.replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt').replace('"', '&quot;').replace(
                "'", '&apos;').encode('utf-8')

        es_neo = self.env['ir.config_parameter'].search([('key', '=', 'neo')])
        token = None
        _uuid = str(uuid.uuid4()).upper()
        if not invoice.journal_id.mpfel_type:
            return
        elif invoice.journal_id.mpfel_type == '':
            return
        elif not invoice.invoice_date:
            raise UserError(_('Missing document date'))
        elif self.token_due_date:
            if self.token_due_date >= fields.Datetime.now():
                if not invoice.mpfel_void_uuid:
                    invoice.mpfel_void_uuid = _uuid

                current_date = datetime.now().replace(tzinfo=pytz.utc).astimezone(pytz.timezone(self.env.user.tz))
                current_time = current_date.strftime('T%H:%M:%S-06:00')

                if invoice.journal_id.mpfel_type == 'FESP':
                    # Factura especial
                    _NITReceptor = invoice.partner_id.x_dpi if invoice.partner_id.x_dpi else invoice.partner_id.ref.replace(
                        '-', '') or invoice.partner_id.ref.replace('-', '') if invoice.partner_id.ref.replace('-',
                                                                                                              '') else 'CF'
                    # TipoEspecial="EXT" --> cundo es pasaporte falta validar
                else:
                    _NITReceptor = invoice.partner_id.vat.replace('-', '') if invoice.partner_id.vat.replace('-','') else 'CF'
                xml = """
                <ns:GTAnulacionDocumento xmlns:ns="http://www.sat.gob.gt/dte/fel/0.1.0" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" Version="0.1">
                   <ns:SAT>
                      <ns:AnulacionDTE ID="DatosCertificados">
                         <ns:DatosGenerales ID="DatosAnulacion" 
                           NumeroDocumentoAAnular="{NumeroDocumentoAAnular}"
                           NITEmisor="{NITEmisor} " 
                           IDReceptor="{IDReceptor} "
                           FechaEmisionDocumentoAnular="{FechaEmisionDocumentoAnular}"
                           FechaHoraAnulacion="{FechaHoraAnulacion}"
                           MotivoAnulacion="Anulacion" />
                      </ns:AnulacionDTE>
                   </ns:SAT>
                </ns:GTAnulacionDocumento>""".format(
                    NumeroDocumentoAAnular=invoice.mpfel_sat_uuid,
                    NITEmisor=invoice.company_id.vat.replace('-', '') if invoice.company_id.vat else 'C/F',
                    IDReceptor=invoice.partner_id.ref.replace('-', '') if invoice.partner_id.ref else 'CF',
                    FechaEmisionDocumentoAnular=invoice.date_sign,
                    FechaHoraAnulacion=current_date.replace(microsecond=1).isoformat().replace('.000001', '.000'),
                    MotivoAnulacion='ANULACION',
                )
                print(xml)
                headers = {
                    'Content-Type': 'application/xml',

                    'Authorization': 'Bearer {}'.format(self.token)
                }
                data = """<?xml version="1.0" encoding="UTF-8" ?>
                    <FirmaDocumentoRequest id="{}">
                    <xml_dte><![CDATA[{}]]></xml_dte>
                    </FirmaDocumentoRequest>
                """.format(_uuid, xml)
                print(data)
                response = requests.post(self.ws_url_signer, data=data, headers=headers)
                result = xmltodict.parse(response.text)
                xml2 = unescape(response.text).encode('utf-8')



                xml3 = response.text.replace('&lt;', '<')
                xml3 = xml3.replace('&gt;', '>')
                xml2 = xml3





                source_xml = xml
                sign_document = False
                if result[u'FirmaDocumentoResponse'][u'listado_errores'] == None:
                    sign_document = True

                error_message = ''
                if sign_document:
                    pos = xml2.find('<ns:GTAnulacionDocumento')
                    if pos >= 0:
                        end = xml2.find('</ns:GTAnulacionDocumento>', pos)
                        doc = unescape(xml2[pos:end + 26])

                    headers = {
                        'Content-Type': 'application/xml',
                        'Authorization': 'Bearer {}'.format(self.token)
                    }
                    data = '<?xml version="1.0" encoding="UTF-8" standalone="no"?><AnulaDocumentoXMLRequest id="{}"><xml_dte><![CDATA[{}]]></xml_dte></AnulaDocumentoXMLRequest>'.format(
                        invoice.mpfel_void_uuid.upper(), doc)

                    try:
                        response = requests.post(self.ws_url_void, headers=headers, data=data)
                        if response.ok:
                            result = xmltodict.parse(response.text)
                            if result['AnulaDocumentoXMLResponse']['tipo_respuesta'] == '1':
                                error_message = ''
                                if bool(result['AnulaDocumentoXMLResponse']['listado_errores']['error']):
                                    error_message += '\n{}: {}'.format(
                                        result['AnulaDocumentoXMLResponse']['listado_errores']['error']['cod_error'],
                                        result['AnulaDocumentoXMLResponse']['listado_errores']['error']['desc_error'])
                                else:
                                    error_message += '\n{}: {}'.format(
                                        result['AnulaDocumentoXMLResponse']['listado_errores']['error']['cod_error'],
                                        result['AnulaDocumentoXMLResponse']['listado_errores']['error']['desc_error'])
                                raise UserError(error_message)
                            else:
                                invoice.write({
                                    'mpfel_void_sat_uuid': result['AnulaDocumentoXMLResponse']['uuid'],
                                    'mpfel_void_source_xml': source_xml,
                                    'mpfel_void_signed_xml': doc,
                                    'mpfel_void_result_xml': result['AnulaDocumentoXMLResponse']['xml_dte'],
                                })
                                invoice.button_draft()
                                invoice.button_cancel()

                        else:
                            raise ValidationError(
                                _('MPFEL: Response error consuming web service: {}').format(str(response.text)))
                    except ValidationError as e:
                        if len(error_message) <= 2:
                            error_message = ''
                        if hasattr(e, 'object'):
                            if hasattr(e, 'reason'):
                                error_message += u"{}: {}".format(e.reason, e.object)
                            else:
                                error_message += u" {}".format(e.object)
                        elif hasattr(e, 'message'):
                            error_message += e.message
                        elif hasattr(e, 'name'):
                            error_message += e.name
                        else:
                            error_message += e
                        raise ValidationError(_('MPFEL: Error consuming web service: {}').format(error_message))
                else:
                    raise ValidationError(_('MPFEL: API key not set'))
            else:
                raise ValidationError(_('MPFEL: Token expired'))
        else:
            raise ValidationError(_('MPFEL: Token not set'))




class pos_order_fel(models.Model):
    _name = "pos.order"
    _inherit = "pos.order"

    infilefel_comercial_name = fields.Char(string='Comercial name' )
    serie_venta = fields.Char('Serie ventas')
    infilefel_establishment_street = fields.Char('Establishment street')


    nit_certificador = fields.Char('Nit empresa certificadora')
    nombre_certificador = fields.Char('Nombre empresa certificadora ')
    frase_certificador = fields.Char('Frase empresa o cliente')


    nit_empresa = fields.Char('Nit empresa')
    nombre_empresa = fields.Char('Nombre empresa')

    infile_number = fields.Char('Número DTE')
    infilefel_sat_uuid = fields.Char('SAT UUID')
    infilefel_sign_date = fields.Char('Sign date')

    nombre_cliente = fields.Char('Nombre cliente')
    nit = fields.Char('Nit cliente')
    direccion_cliente = fields.Char('Dirección cliente')
    fecha_factura = fields.Char('Fecha factura')


    caja = fields.Char('Caja')
    vendedor = fields.Char('Vendedor')
    forma_pago = fields.Char('Forma pago')

