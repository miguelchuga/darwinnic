# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
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
import pyPdf

from tempfile import gettempdir

class mpfel_settings(models.Model):
    _name = "mpfel.settings"
    _description = "Megaprint FEL settings"

    ws_url_token = fields.Char('Token web service URL', default = 'https://')
    ws_url_document = fields.Char('Document web service URL', default = 'https://')
    ws_url_void = fields.Char('Void document web service URL', default = 'https://')
    ws_url_pdf = fields.Char('Void document web service URL', default = 'https://')
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

    @api.multi
    def get_token(self):
        if self.ws_url_token:
            if self.user:
                if self.api_key:
                    headers = {
                        'Content-Type': 'application/xml',
                    }
                    data = "<SolicitaTokenRequest><usuario>{}</usuario><apikey>{}</apikey></SolicitaTokenRequest>".format(self.user, self.api_key)
                    try:
                        response = requests.post(self.ws_url_token, headers=headers, data=data)
                        if response.ok:
                            text = ElementTree.fromstring(response.text)
                            token_tag = text.findall('token')
                            if token_tag:
                                self.token = token_tag[0].text
                            due_date_tag = text.findall('vigencia')
                            if due_date_tag:
                                token_due_date = datetime.strptime(due_date_tag[0].text[:19], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.timezone(self.env.user.tz))
                                self.token_due_date = token_due_date
                    except Exception, e:
                        raise UserError(_('MPFEL: Error consuming web service: {}').format(e.message))
                else:
                    raise UserError( _('MPFEL: API key not set'))
            else:
                raise UserError(_('MPFEL: User not set'))
        else:
            raise UserError(_('MPFEL: Web service URL for tokens not set'))

    @api.multi
    def sign_document(self, invoice):

        def escape_string(value):
            return value.replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt').replace('"', '&quot;').replace("'", '&apos;').encode('utf-8')

        token = None
        if not invoice.journal_id.mpfel_type:
            return
        elif invoice.journal_id.mpfel_type == '':
            return
        elif invoice.mpfel_sat_uuid:
            return
 #           raise UserError(_('Document is already signed'))
        elif not invoice.date_invoice:
            raise UserError(_('Missing document date'))
        elif self.token_due_date:
            if self.token_due_date >= fields.Datetime.now():
                if not invoice.mpfel_uuid:
                    invoice.mpfel_uuid = str(uuid.uuid4())

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
                    if line.invoice_line_tax_ids:
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
                        BienOServicio='B' if line.product_id.type == 'product' or line.product_id.default_code=='BIEN'  else 'S',
                        NumeroLinea=line_number,
                        Cantidad=line.quantity,
                        UnidadMedida=line.uom_id.name[:3],
                        Descripcion=escape_string(line.name),
                        PrecioUnitario=line.price_unit,
                        Precio=line_gross,
                        Descuento=line_discount,
                        TituloImpuestos='' if invoice.journal_id.mpfel_type in ['NABN'] else '<dte:Impuestos>'
                    )
                    line_taxes = 0
                    if invoice.journal_id.mpfel_type not in ['NABN']:
                        for tax_id in line.invoice_line_tax_ids:
                            if tax_id.mpfel_sat_code=='IVA':
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
                    """.format(TituloImpuestos='' if invoice.journal_id.mpfel_type in ['NABN'] else '</dte:Impuestos>', Total=line_amount)

                #
                # Frases
                #
                xml_phrases = ''
                if invoice.journal_id.mpfel_type not in ['NCRE', 'NDEB', 'NABN','FESP']:
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
                invoice_sign_date = invoice.date_invoice + current_time
                date_sign = invoice_sign_date


                if invoice.journal_id.mpfel_type == 'FESP':
                    #Factura especial
                    _NITReceptor = invoice.partner_id.x_dpi if invoice.partner_id.x_dpi else invoice.partner_id.ref.replace('-', '') or invoice.partner_id.ref.replace('-', '') if invoice.partner_id.ref.replace('-', '') else 'CF'
                    #TipoEspecial="EXT" --> cundo es pasaporte falta validar
                else:
                    _NITReceptor = invoice.x_nit_generico.replace('-', '') if invoice.partner_id.x_es_generico  else  invoice.partner_id.ref.replace('-', '') or invoice.partner_id.ref.replace('-', '') if invoice.partner_id.ref.replace('-', '') else 'CF'

                xml = """<?xml version="1.0" encoding="UTF-8"?><dte:GTDocumento Version="0.4" xmlns:dte="http://www.sat.gob.gt/dte/fel/0.1.0" xmlns:xd="http://www.w3.org/2000/09/xmldsig#">
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
                        EXP='',  # Para exportaciones: 'EXP="SI"'
                        FechaHoraEmision=invoice_sign_date,
                        NumeroAcceso='',
                        Tipo=invoice.journal_id.mpfel_type,
                        AfiliacionIVA=self.vat_affiliation,
                        CodigoEstablecimiento=self.organization_code,
                        CorreoEmisor=invoice.company_id.email if invoice.company_id.email else '',
                        NITEmisor=invoice.company_id.vat.replace('-', '') if invoice.company_id.vat else 'C/F',
                        NombreComercial=escape_string(invoice.company_id.name),
                        NombreEmisor=escape_string(invoice.company_id.name),
                        DireccionEmisor=escape_string((invoice.company_id.street if invoice.company_id.street else '') + (' ' + invoice.company_id.street2 if invoice.company_id.street2 else '')),
                        CodigoPostalEmisor=invoice.company_id.zip if invoice.company_id.zip else '01001',
                        MunicipioEmisor=escape_string(invoice.company_id.city if invoice.company_id.city else ''),
                        DepartamentoEmisor=escape_string(invoice.company_id.state_id.name if invoice.company_id.state_id else ''),
                        PaisEmisor=escape_string(invoice.company_id.country_id.code if invoice.company_id.country_id else ''),
                        DireccionReceptor=escape_string((invoice.partner_id.street if invoice.partner_id.street else '') + (' ' + invoice.partner_id.street2 if invoice.partner_id.street2 else '')),
                        CorreoReceptor=invoice.partner_id.email if invoice.partner_id.email else '',

                        NITReceptor= _NITReceptor, #invoice.x_nit_generico.replace('-', '') if invoice.partner_id.x_es_generico  else  invoice.partner_id.ref.replace('-', '') or invoice.partner_id.ref.replace('-', '') if invoice.partner_id.ref.replace('-', '') else 'CF',                        

                        NombreReceptor= escape_string(invoice.x_nombre_generico) if invoice.partner_id.x_es_generico else escape_string(invoice.partner_id.name),
                        _TipoEspecial= 'TipoEspecial="CUI" ' if invoice.journal_id.mpfel_type == 'FESP' else '',

                        CodigoPostal=invoice.partner_id.zip if invoice.partner_id.zip else '01001',
                        Municipio=escape_string(invoice.partner_id.city) if invoice.partner_id.city else '',
                        Departamento=escape_string(invoice.partner_id.state_id.name) if invoice.partner_id.state_id else '',
                        Pais=escape_string(invoice.partner_id.country_id.code if invoice.partner_id.country_id else ''),
                        Frases=xml_phrases,
                        Items=xml_lines,
                        TituloImpuestos='' if invoice.journal_id.mpfel_type in ['NABN'] else '<dte:TotalImpuestos>'
                    )
                # xml += """</dte:Items>
                #                 <dte:Totales>
                #                 <dte:TotalImpuestos>
                # """
                if not invoice.journal_id.mpfel_type in ['NABN']:
                    for tax in taxes:
                        xml += '<dte:TotalImpuesto NombreCorto="{NombreCorto}" TotalMontoImpuesto="{TotalMontoImpuesto}"/>'.format(
                            NombreCorto=tax['NombreCorto'],
                            TotalMontoImpuesto=tax['Valor']
                        )

                extras = ''



                if invoice.journal_id.mpfel_type == 'FCAM':
                    #<dte:AbonosFacturaCambiaria Version="1">
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
                                </dte:Complementos>""".format(FechaVencimiento=invoice.date_due, Monto=invoice.amount_total)
                elif invoice.journal_id.mpfel_type in ['FESP']:
                    _iva_especial = 0
                    _isr_especial = 0
                    for _tax in invoice.tax_line_ids:
                        if _tax.tax_id.mpfel_sat_code=='IVA':
                           _iva_especial = _tax.amount
                        if _tax.tax_id.mpfel_sat_code=='ISR':
                            _isr_especial = abs(_tax.amount)

                    extras = """
                                <dte:Complementos>
                                    <dte:Complemento IDComplemento="1" NombreComplemento="RETENCION" URIComplemento="http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0">
                                        <ces:RetencionesFacturaEspecial xmlns:ces="http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0" Version="1">
                                            <ces:RetencionISR>{ISRespecial}</ces:RetencionISR>
                                            <ces:RetencionIVA>{IVAespecial}</ces:RetencionIVA>
                                            <ces:TotalMenosRetenciones>{TOTALespecial}</ces:TotalMenosRetenciones>
                                        </ces:RetencionesFacturaEspecial>
                                    </dte:Complemento>    
                                </dte:Complementos>""".format(ISRespecial=_isr_especial, IVAespecial=_iva_especial,TOTALespecial=invoice.amount_total)
                                

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
                    if invoice.refund_invoice_id:
                        previous_regime = ''
                        original_document = invoice.origin
                        reason = ''
                        if invoice.refund_invoice_id.mpfel_sat_uuid:
                            id_complemento = 'ReferenciasNota'
                            nombre_complemento = 'ReferenciasNota'
                            original_document = invoice.refund_invoice_id.mpfel_sat_uuid
                            reason = 'MotivoAjuste="{}"'.format(invoice.name)

                        else:
                            id_complemento = 'ComplementoReferenciaNota'
                            nombre_complemento = 'Complemento Referencia Nota'
                            previous_regime = 'RegimenAntiguo="Antiguo"'
#                            original_document = invoice.refund_invoice_id.journal_id.mpfel_previous_authorization
                            original_document = invoice.refund_invoice_id.resolution_id.name
#                            reason = 'SerieDocumentoOrigen="{}" NumeroDocumentoOrigen="{}"'.format(invoice.refund_invoice_id.journal_id.mpfel_previous_serial, invoice.refund_invoice_id.name)
                            reason = 'SerieDocumentoOrigen="{}" NumeroDocumentoOrigen="{}"'.format(invoice.refund_invoice_id.gface_dte_serial[8:9], str(int(invoice.refund_invoice_id.gface_dte_number[16:100])) )

                        references = references.format(
                            RegimenAnterior=previous_regime,
                            DocumentoOrigen=original_document,
                            FechaEmision=invoice.refund_invoice_id.date_invoice,
                            MotivoAjuste=reason,
                        )
                    else:
                        id_complemento = 'ComplementoReferenciaNota'
                        nombre_complemento = 'Complemento Referencia Nota'
#                        reason = 'SerieDocumentoOrigen="{}" NumeroDocumentoOrigen="{}"'.format(invoice.journal_id.mpfel_previous_serial, invoice.name)
                        reason = 'SerieDocumentoOrigen="{}" NumeroDocumentoOrigen="{}"'.format(invoice.refund_invoice_id.gface_dte_serial, invoice.refund_invoice_id.resolution_id.name)
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

                #PARA GENERAR EL PDF NECESITA LOS DATOS EXTRAS EN ADENDAS
                if not self.ws_url_pdf:
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
                """.format(NoPedido = invoice.origin,OrdenCompra = invoice.x_orden,Vendedor = invoice.user_id.name)           

                    adendasitem = ''
                    line_number = 0
                    for line in invoice.invoice_line_ids:
                        line_number += 1
                        line_str= str(line_number)
                        item = line.product_id.default_code
                        adendasitem += """
		   		        <dte:AdendaItem LineaReferencia="{Line_str}">
					        <dte:Valor1>{Item}</dte:Valor1>
				        </dte:AdendaItem>
                        """.format(Line_str=line_str,Line_strA=line_str, Line_strB=line_str,Item = item)

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
                  </dte:GTDocumento>""".format(TituloImpuestos='' if invoice.journal_id.mpfel_type in ['NABN'] else '</dte:TotalImpuestos>', GranTotal= line_amount if invoice.journal_id.mpfel_type in ['FESP'] else invoice.amount_total, Complementos=extras,adendas=adendas,adendasitem=adendasitem)



                source_xml = xml
                print xml
#                tmp_dir = gettempdir()
                tmp_dir = self.path_xml

                sign_document = False
                if self.signing_type == 'LOCAL':
#                    tmp_dir = gettempdir()
                    source_xml_file = os.path.join(tmp_dir, '{}_source.xml'.format(invoice.mpfel_uuid))
                    signed_xml_file = os.path.join(tmp_dir, '{}.xml'.format(invoice.mpfel_uuid))
                    with open(source_xml_file, 'w') as xml_file:
                        xml_file.write(xml)
                    # os.system('java -jar {} {} {} {} {}'.format('/Users/oscar/Desarrollo/java/XadesMPFEL.jar', source_xml_file, '/tmp/39796558-28d66a63138ff444.pfx', "'Neo2018$1'", invoice.mpfel_uuid))
                    os.system("java -jar {} {} {} '{}' {} {} {}".format(self.signer_location, source_xml_file, self.certificate_file, self.certificate_password, invoice.mpfel_uuid, tmp_dir, 'DatosEmision'))

                    if os.path.isfile(signed_xml_file):
                        with open(signed_xml_file, 'r') as myfile:
                            xml = myfile.read()
                        sign_document = True
                    else:
                        raise UserError(_('MPFEL: Signed XML file not found'))
                else:
                    sign_response = requests.post(url=self.ws_url_signer, data={'XML': xml, 'UUID': invoice.mpfel_uuid, 'Main_Tag': 'DatosEmision'})
                    result = json.loads(sign_response.text)
                    if result['success']:
                        xml = result['signed_xml'].encode('utf-8')
                        sign_document = True
                    else:
                        raise UserError(_('Error signing document: {}').format(result['message']))

                error_message = ''
                if sign_document:
                    if self.token:
                        headers = {
                            'Content-Type': 'application/xml',
                            'Authorization': 'Bearer {}'.format(self.token)
                        }
                        data = '<?xml version="1.0" encoding="UTF-8" standalone="no"?><RegistraDocumentoXMLRequest id="{}"><xml_dte><![CDATA[{}]]></xml_dte></RegistraDocumentoXMLRequest>'.format(invoice.mpfel_uuid.upper(), xml)
                        try:
                            response = requests.post(self.ws_url_document, headers=headers, data=data)
                            if response.ok:
                                result = xmltodict.parse(response.text)
                                if result['RegistraDocumentoXMLResponse']['tipo_respuesta'] == '1':
                                    error_message = u''
                                    if type(result['RegistraDocumentoXMLResponse']['listado_errores']['error']) is list:
#                                    if bool(result['RegistraDocumentoXMLResponse']['listado_errores']['error']):
                                        for message in result['RegistraDocumentoXMLResponse']['listado_errores']['error']:
                                            error_message += '\n{}: {}'.format(message['cod_error'], message['desc_error'])
#                                         error_message += '\n{}: {}'.format(result['RegistraDocumentoXMLResponse']['listado_errores']['error']['cod_error'], result['RegistraDocumentoXMLResponse']['listado_errores']['error']['desc_error'])

                                    else:
                                        error_message += '\n{}: {}'.format(result['RegistraDocumentoXMLResponse']['listado_errores']['error']['cod_error'], result['RegistraDocumentoXMLResponse']['listado_errores']['error']['desc_error'])
                                    raise UserError(error_message)
                                else:

                                    _mpfel_serial = ''
                                    _mpfel_number = ''

                                    _sat_uuid = str(result['RegistraDocumentoXMLResponse']['uuid']).split('-')
                                    _count = 0
                                    for a in _sat_uuid:
                                        if _count == 0:
                                            _mpfel_serial = a
                                        if _count == 1 or  _count == 2:                                                                 
                                            _mpfel_number += a
                                        _count += 1

                                                                             
                                    print xml 
                                    if invoice.journal_id.ws_url_pdf:
                                        pdf_headers = {
                                            'Content-Type': 'application/xml',
                                            'Authorization': 'Bearer {}'.format(self.token)
                                        }
                                        _sat_uid = result['RegistraDocumentoXMLResponse']['uuid']
                                        pdf_data = """<RetornaPDFRequest>                                                    
                                                   <uuid>{ThisisaUUID}</uuid>
                                                </RetornaPDFRequest>
                                              """.format(
                                                          ThisisaUUID=_sat_uid
                                                        )
                                        pdf_response = requests.post(url=invoice.journal_id.ws_url_pdf,headers=pdf_headers, data=pdf_data)
                                        result_pdf = xmltodict.parse(pdf_response.text)
                                        _pdf = result_pdf['RetornaPDFResponse']['pdf']

                                    if invoice.journal_id.tipo_venta == 'ND':
                                        _data = {
                                            'mpfel_pdf':_pdf  if invoice.journal_id.ws_url_pdf else '',
                                            'mpfel_file_name':_sat_uid+'.'+'pdf' if invoice.journal_id.ws_url_pdf  else '',
                                            'type': 'out_invoice' ,
                                            'amount_total_company_signed':invoice.amount_total_company_signed*-1,
                                            'residual_company_signed':invoice.residual_company_signed*-1,
                                            'amount_total_signed':invoice.amount_total_signed*-1,
                                            'residual_signed':invoice.residual_signed*-1,
                                            'amount_untaxed_signed':invoice.amount_untaxed_signed*-1,
                                            'mpfel_sign_date': invoice_sign_date,
                                            'mpfel_sat_uuid': result['RegistraDocumentoXMLResponse']['uuid'],
                                            'mpfel_source_xml': source_xml,
                                            'mpfel_signed_xml': xml,
                                            'mpfel_result_xml': result['RegistraDocumentoXMLResponse']['xml_dte'],
                                            'mpfel_serial':_mpfel_serial,
                                            'mpfel_number':str(int(_mpfel_number,16)),
                                            'number':_mpfel_serial+'-'+str(int(_mpfel_number,16)),
                                            'move_name':_mpfel_serial+'-'+str(int(_mpfel_number,16)),
                                            'date_sign':date_sign,}
                                    else:
                                        _data = {
                                            'mpfel_pdf':_pdf if invoice.journal_id.ws_url_pdf  else '',
                                            'mpfel_file_name':_sat_uid+'.'+'pdf' if invoice.journal_id.ws_url_pdf  else '',
                                            'mpfel_sat_uuid': result['RegistraDocumentoXMLResponse']['uuid'],
                                            'mpfel_source_xml': source_xml,
                                            'mpfel_signed_xml': xml,
                                            'mpfel_result_xml': result['RegistraDocumentoXMLResponse']['xml_dte'],
                                            'mpfel_serial':_mpfel_serial,
                                            'mpfel_number':str(int(_mpfel_number,16)),
                                            'number':_mpfel_serial+'-'+str(int(_mpfel_number,16)),
                                            'move_name':_mpfel_serial+'-'+str(int(_mpfel_number,16)),
                                            'date_sign':date_sign,
                                            'mpfel_sign_date':invoice_sign_date,
                                        }                              

                                    invoice.write(_data)

                            else:
                                raise UserError(_('MPFEL: Response error consuming web service: {}').format(str(response.text)))
                        except Exception, e:
                            if len(error_message)<=2:
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
                            raise UserError(_('MPFEL: Error consuming web service: {}').format(error_message))
                    else:
                        raise UserError(_('MPFEL: API key not set'))
                else:
                    raise UserError(_('MPFEL Signer: {}').format(result['message']))
            else:
                raise UserError(_('MPFEL: Token expired'))
        else:
            raise UserError(_('MPFEL: Token not set'))

    @api.multi
    def void_document(self, invoice):

        def escape_string(value):
            return value.replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt').replace('"', '&quot;').replace("'", '&apos;').encode('utf-8')

        token = None
        if not invoice.journal_id.mpfel_type:
            return
        elif invoice.journal_id.mpfel_type == '':
            return
        elif not invoice.date_invoice:
            raise UserError(_('Missing document date'))
        elif self.token_due_date:
            if self.token_due_date >= fields.Datetime.now():
                if not invoice.mpfel_void_uuid:
                    invoice.mpfel_void_uuid = str(uuid.uuid4())

                current_date = datetime.now().replace(tzinfo=pytz.utc).astimezone(pytz.timezone(self.env.user.tz))
                current_time = current_date.strftime('T%H:%M:%S-06:00')

                if invoice.journal_id.mpfel_type == 'FESP':
                    #Factura especial
                    _NITReceptor = invoice.partner_id.x_dpi if invoice.partner_id.x_dpi else invoice.partner_id.ref.replace('-', '') or invoice.partner_id.ref.replace('-', '') if invoice.partner_id.ref.replace('-', '') else 'CF'
                    #TipoEspecial="EXT" --> cundo es pasaporte falta validar
                else:
                    _NITReceptor = invoice.x_nit_generico.replace('-', '') if invoice.partner_id.x_es_generico  else  invoice.partner_id.ref.replace('-', '') or invoice.partner_id.ref.replace('-', '') if invoice.partner_id.ref.replace('-', '') else 'CF'


#                <?xml version="1.0" encoding="UTF-8"?>
#                <ns:GTAnulacionDocumento Version="0.1" xmlns:dte="http://www.sat.gob.gt/dte/fel/0.1.0" xmlns:xd="http://www.w3.org/2000/09/xmldsig#">
#{_TipoEspecial}
                xml = """
                <ns:GTAnulacionDocumento xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:ns="http://www.sat.gob.gt/dte/fel/0.1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"  Version="0.1" >


                <ns:SAT>
                    <ns:AnulacionDTE ID="DatosCertificados">
                        <ns:DatosGenerales ID="DatosAnulacion"
                            NumeroDocumentoAAnular="{NumeroDocumentoAAnular}"
                            NITEmisor="{NITEmisor} "
                            IDReceptor="{IDReceptor} "
                            FechaEmisionDocumentoAnular="{FechaEmisionDocumentoAnular}"
                            FechaHoraAnulacion="{FechaHoraAnulacion}"
                            MotivoAnulacion="Cancelacion"
                        />



                    </ns:AnulacionDTE>
                </ns:SAT></ns:GTAnulacionDocumento>""".format(
                        NumeroDocumentoAAnular=invoice.mpfel_sat_uuid,
                        NITEmisor=invoice.company_id.vat.replace('-', '') if invoice.company_id.vat else 'C/F',
                        NITReceptor=  _NITReceptor, #invoice.x_nit_generico.replace('-', '') if invoice.partner_id.x_es_generico  else  invoice.partner_id.ref.replace('-', '') or invoice.partner_id.ref.replace('-', '') if invoice.partner_id.ref.replace('-', '') else 'CF',                        
#                        _TipoEspecial= 'TipoEspecial="CUI" ' if invoice.journal_id.mpfel_type == 'FESP' else '',

                        IDReceptor= invoice.x_nit_generico.replace('-', '') if invoice.partner_id.x_es_generico  else  invoice.partner_id.ref.replace('-', '') or invoice.partner_id.ref.replace('-', '') if invoice.partner_id.ref.replace('-', '') else 'CF',

                        FechaEmisionDocumentoAnular= invoice.date_sign,#"{}T{}-06:00".format(invoice.mpfel_sign_date[:10], invoice.mpfel_sign_date[11:]),
                        FechaHoraAnulacion=current_date.replace(microsecond=1).isoformat().replace('.000001', '.000'),
#                        NITCertificador=invoice.company_id.vat.replace('-', '') if invoice.company_id.vat else 'C/F',
#                        NombreCertificador=invoice.company_id.name,
#                        FechaHoraCertificacion=invoice.date_invoice+'T'+time.strftime("%H:%M:%S")+'-06:00',     #invoice.date_invoice + 'T00:00:00-06:00',
                    )

#                        <dte:Certificacion>
#                            <dte:NITCertificador>{NITCertificador}</dte:NITCertificador>
#                            <dte:NombreCertificador>{NombreCertificador}</dte:NombreCertificador>
#                            <dte:FechaHoraCertificacion>{FechaHoraCertificacion}</dte:FechaHoraCertificacion>
#                        </dte:Certificacion>


                source_xml = xml
                print source_xml
                # tmp_dir = gettempdir()
                # source_xml_file = os.path.join(tmp_dir, '{}_source.xml'.format(invoice.mpfel_void_uuid))
                # signed_xml_file = os.path.join(tmp_dir, '{}.xml'.format(invoice.mpfel_void_uuid))
                # with open(source_xml_file, 'w') as xml_file:
                #     xml_file.write(xml)
                # os.system("java -jar {} {} {} '{}' {} {} {}".format(self.signer_location, source_xml_file, self.certificate_file, self.certificate_password, invoice.mpfel_void_uuid, tmp_dir, 'DatosGenerales'))
                #
                # if not os.path.isfile(signed_xml_file):
                #     raise UserError(_('MPFEL: Signed XML file not found'))
                # elif self.token:
                sign_document = False
                if self.signing_type == 'LOCAL':
                    tmp_dir = self.path_xml
                    print tmp_dir
                    print "================================="

#tmp_dir = gettempdir()
                    source_xml_file = os.path.join(tmp_dir, '{}_source.xml'.format(invoice.mpfel_void_uuid))
                    signed_xml_file = os.path.join(tmp_dir, '{}.xml'.format(invoice.mpfel_void_uuid))
                    with open(source_xml_file, 'w') as xml_file:
                        xml_file.write(xml)
                    # os.system('java -jar {} {} {} {} {}'.format('/Users/oscar/Desarrollo/java/XadesMPFEL.jar', source_xml_file, '/tmp/39796558-28d66a63138ff444.pfx', "'Neo2018$1'", invoice.mpfel_uuid))
                    os.system("java -jar {} {} {} '{}' {} {} {}".format(self.signer_location, source_xml_file, self.certificate_file, self.certificate_password, invoice.mpfel_void_uuid, tmp_dir, 'DatosGenerales'))

                    if os.path.isfile(signed_xml_file):
                        with open(signed_xml_file, 'r') as myfile:
                            xml = myfile.read()
                        sign_document = True
                    else:
                        raise UserError(_('MPFEL: Signed XML file not found'))
                else:
                    sign_response = requests.post(url=self.ws_url_signer, data={'XML': xml, 'UUID': invoice.mpfel_void_uuid, 'Main_Tag': 'DatosGenerales'})
                    result = json.loads(sign_response.text)
                    if result['success']:
                        xml = result['signed_xml'].encode('utf-8')
                        sign_document = True
                    else:
                        raise UserError(_('Error signing document: {}').format(result['message']))
                error_message = ''
                if sign_document:
                    headers = {
                        'Content-Type': 'application/xml',
                        'Authorization': 'Bearer {}'.format(self.token)
                    }
                    data = '<?xml version="1.0" encoding="UTF-8" standalone="no"?><AnulaDocumentoXMLRequest id="{}"><xml_dte><![CDATA[{}]]></xml_dte></AnulaDocumentoXMLRequest>'.format(invoice.mpfel_void_uuid.upper(), xml)
                    print data
                    try:
                        response = requests.post(self.ws_url_void, headers=headers, data=data)
                        if response.ok:
                            result = xmltodict.parse(response.text)
                            if result['AnulaDocumentoXMLResponse']['tipo_respuesta'] == '1':
                                error_message = ''
                                if bool(result['AnulaDocumentoXMLResponse']['listado_errores']['error']):
#                                    for message in result['RegistraDocumentoXMLResponse']['listado_errores']['error']:
#                                        error_message += '\n{}: {}'.format(message['cod_error'], message['desc_error'])
                                     error_message += '\n{}: {}'.format(result['AnulaDocumentoXMLResponse']['listado_errores']['error']['cod_error'], result['AnulaDocumentoXMLResponse']['listado_errores']['error']['desc_error'])

#                                if type(result['AnulaDocumentoXMLResponse']['listado_errores']['error']) is list:
#                                    for message in result['AnulaDocumentoXMLResponse']['listado_errores']['error']:
#                                        error_message += '\n{}: {}'.format(message['cod_error'], message['desc_error'])
                                else:
                                    error_message += '\n{}: {}'.format(result['AnulaDocumentoXMLResponse']['listado_errores']['error']['cod_error'], result['AnulaDocumentoXMLResponse']['listado_errores']['error']['desc_error'])
                                raise UserError(error_message)
                            else:
                                invoice.write({
#                                    'state':'cancel',                                               
                                    'mpfel_void_sat_uuid': result['AnulaDocumentoXMLResponse']['uuid'],
                                    'mpfel_void_source_xml': source_xml,
                                    'mpfel_void_signed_xml': xml,
                                    'mpfel_void_result_xml': result['AnulaDocumentoXMLResponse']['xml_dte'],
                                })
                                invoice.action_invoice_cancel()

                        else:
                            raise UserError(_('MPFEL: Response error consuming web service: {}').format(str(response.text)))
                    except Exception, e:
                        if len(error_message)<=2:
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
                        raise UserError(_('MPFEL: Error consuming web service: {}').format(error_message))
                else:
                    raise UserError(_('MPFEL: API key not set'))
            else:
                raise UserError(_('MPFEL: Token expired'))
        else:
            raise UserError(_('MPFEL: Token not set'))

class mpfel_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = "mpfel.config.settings"
    _description = "Megaprint FEL settings configurator"

    default_ws_url_token = fields.Char('Token web service URL', default_model='mpfel.config.settings')
    default_ws_url_document = fields.Char('Document web service URL', default_model='mpfel.config.settings')
    default_ws_url_void = fields.Char('Void document web service URL', default_model='mpfel.config.settings')
    default_ws_url_pdf = fields.Char('PDF document web service URL', default_model='mpfel.config.settings')
    default_ws_url_signer = fields.Char('Signer web service URL', default_model='mpfel.config.settings')
    default_ws_timeout = fields.Integer('Web service timeout', default_model='mpfel.config.settings')
    default_user = fields.Char('User', default_model='mpfel.config.settings')
    default_api_key = fields.Char('API Key', default_model='mpfel.config.settings')
    default_token = fields.Char('Token', default_model='mpfel.config.settings')
    default_token_due_date = fields.Datetime('Token due date', default_model='mpfel.config.settings')
    default_megaprint_vat = fields.Char('Megaprint VAT', default_model='mpfel.config.settings')
    default_certificate_file = fields.Char('Certificate file', default_model='mpfel.config.settings')
    default_path_xml = fields.Char('path xml file', default_model='mpfel.config.settings')
    default_certificate_password = fields.Char('Certificate password', default_model='mpfel.config.settings')
    default_signing_type = fields.Selection([
        ('LOCAL', 'Sign documents using local program'),
        ('WS', 'Sign documents using Web Service'),
    ], string='Signing type', default_model='mpfel.config.settings')
    default_signer_location = fields.Char('Signer program location', default_model='mpfel.config.settings')
    default_organization_code = fields.Char('Organization code', default_model='mpfel.config.settings')
    default_vat_affiliation = fields.Selection([
        ('GEN', 'GEN'),
        ('EXE', 'EXE'),
        ('PEQ', 'PEQ'),
    ], string='VAT affiliation', default_model='mpfel.config.settings')
    default_isr_scenery = fields.Char('ISR scenery', default_model='mpfel.config.settings')
    default_isr_phrases = fields.Char('ISR phrases', default_model='mpfel.config.settings')
    default_excempt_scenery = fields.Char('Excempt scenery', default_model='mpfel.config.settings')

    @api.multi
    def execute(self):
        ret = super(mpfel_config_settings, self).execute()
        if ret:
            values = {
                'ws_url_token': self.default_ws_url_token,
                'ws_url_document': self.default_ws_url_document,
                'ws_url_void': self.default_ws_url_void,
                'ws_url_pdf': self.default_ws_url_pdf,
                'ws_url_signer': self.default_ws_url_signer,
                'ws_timeout': self.default_ws_timeout,
                'user': self.default_user,
                'api_key': self.default_api_key,
                'token': self.default_token,
                'token_due_date': self.default_token_due_date,
                'megaprint_vat': self.default_megaprint_vat,
                'certificate_file': self.default_certificate_file,
                'path_xml': self.default_path_xml,
                'certificate_password': self.default_certificate_password,
                'signing_type': self.default_signing_type,
                'signer_location': self.default_signer_location,
                'organization_code': self.default_organization_code,
                'vat_affiliation': self.default_vat_affiliation,
                'isr_scenery': self.default_isr_scenery,
                'isr_phrases': self.default_isr_phrases,
                'excempt_scenery': self.default_excempt_scenery,
            }
            settings = self.env['mpfel.settings'].search([])
            if settings:
                settings[0].write(values)
            else:
                settings = self.env['mpfel.settings'].create(values)
        return ret

    @api.multi
    def get_token(self):
        # settings = self.env['mpfel.settings'].search([])
        # if settings:
        #     settings = settings[0]
        #     settings.get_token()
        # else:
        #     raise UserError(_('MPFEL: You must first save the settings'))
        if self.default_ws_url_token:
            if self.default_user:
                if self.default_api_key:
                    headers = {
                        'Content-Type': 'application/xml',
                    }
                    data = "<SolicitaTokenRequest><usuario>{}</usuario><apikey>{}</apikey></SolicitaTokenRequest>".format(self.default_user, self.default_api_key)
                    try:
                        response = requests.post(self.default_ws_url_token, headers=headers, data=data)
                    except Exception, e:
                        raise UserError(_('MPFEL: Error consuming web service: {}').format(e.message))
                    if response:
                        if response.ok:
                            result = xmltodict.parse(response.text)
                            if result['SolicitaTokenResponse']['tipo_respuesta'] == '1':
                                error_message = ''
                                if type(result['SolicitaTokenResponse']['listado_errores']['error']) is list:
                                    for message in result['SolicitaTokenResponse']['listado_errores']['error']:
                                        error_message += '\n{}: {}'.format(message['cod_error'], message['desc_error'])
                                else:
                                    error_message += '\n{}: {}'.format(
                                        result['SolicitaTokenResponse']['listado_errores']['error']['cod_error'],
                                        result['SolicitaTokenResponse']['listado_errores']['error']['desc_error'])
                                raise UserError(_('MPFEL Errors {}'.format(error_message)))
                            else:
                                text = ElementTree.fromstring(response.text)
                                token_tag = text.findall('token')
                                if token_tag:
                                    self.default_token = token_tag[0].text
                                due_date_tag = text.findall('vigencia')
                                if due_date_tag:
                                    token_due_date = datetime.strptime(due_date_tag[0].text[:19], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.timezone(self.env.user.tz))
                                    self.default_token_due_date = token_due_date
                                self.execute()
                else:
                    raise UserError(_('MPFEL: API key not set'))
            else:
                raise UserError(_('MPFEL: User not set'))
        else:
            raise UserError(_('MPFEL: Web service URL for tokens not set'))
