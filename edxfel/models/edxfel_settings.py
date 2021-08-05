# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import xml.etree.cElementTree as ElementTree
from datetime import datetime, timedelta
import pytz
import time
import uuid
import xmltodict
import os
import json
from tempfile import gettempdir
import html
import base64


class edxfel_settings(models.Model):
    _name = "edxfel.settings"
    _description = "Edx FEL settings"


    company_id = fields.Many2one("res.company", string="Empresa")
    ws_url_document = fields.Char('Document web service URL', default='https://')
    ws_timeout = fields.Integer('Web service timeout', default=300)
    user = fields.Char('Certification user')
    sign_area = fields.Char('Sign area')
    sign_connector = fields.Char('Sign connector')
    sign_convertdocument = fields.Boolean('Sign ConvertDocument')
    sign_signdocument = fields.Boolean('Sign SignDocument')
    sign_printdocument = fields.Boolean('Sign PrintDocument')

    vat_affiliation = fields.Selection([
        ('GEN', 'GEN'),
        ('EXE', 'EXE'),
        ('PEQ', 'PEQ'),
    ], string='VAT affiliation', default='GEN')
    isr_scenery = fields.Char('ISR sceneries')
    isr_phrases = fields.Char('ISR phrases')
    excempt_scenery = fields.Char('Excempt scenery')


    def sign_document(self, invoice):

        def escape_string(value):
            return html.escape(value).encode("ascii", "xmlcharrefreplace").decode('utf8')

        if not invoice.date_invoice:
            _data = {'date_invoice':(time.strftime("%Y/%m/%d")),
                     'date_due':(time.strftime("%Y/%m/%d")),
                     }
            invoice.write(_data)

        token = None
        if not invoice.journal_id.edxfel_type:
            return
        elif invoice.journal_id.edxfel_type == '':
            return
        elif invoice.edxfel_sat_uuid:
            raise UserError(_('Document is already signed'))
        elif not invoice.date_invoice:
            raise UserError(_('Missing document date'))
        else:
            parter_vat = invoice.partner_id.vat.replace('-', '') if invoice.partner_id.vat else 'CF'
            partner_name = escape_string(invoice.partner_id.name)
            if not invoice.edxfel_uuid:
                invoice.edxfel_uuid = str(uuid.uuid4())

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
                    BienOServicio='S' if line.product_id.type == 'service' else 'B',
                    NumeroLinea=line_number,
                    Cantidad=round(line.quantity,2),
                    UnidadMedida=escape_string(line.uom_id.name)[:3],
                    Descripcion=escape_string(line.name),
                    PrecioUnitario=round(line.price_unit,2),
                    Precio="{0:.2f}".format(round(line_gross,2)),
                    Descuento="{0:.2f}".format(round(line_discount,2)),
                    TituloImpuestos='' if invoice.journal_id.edxfel_type in ['NABN'] else '<dte:Impuestos>'
                )
                # UnidadMedida = escape_string(line.uom_id.name[:3]),

                line_taxes = 0
                if invoice.journal_id.edxfel_type not in ['NABN']:
                    for tax_id in line.invoice_line_tax_ids:
                        amount = 0
                        if invoice.journal_id.edxfel_type not in ['NABN'] and tax_id.amount_type == 'percent':
                            amount = round(line_amount * tax_id.amount / (100 + tax_id.amount), 2)
                        line_taxes += amount
                        xml_lines += """<dte:Impuesto>
                                <dte:NombreCorto>{NombreCorto}</dte:NombreCorto>
                                <dte:CodigoUnidadGravable>{CodigoUnidadGravable}</dte:CodigoUnidadGravable>
                                <dte:MontoGravable>{MontoGravable}</dte:MontoGravable>
                                <dte:MontoImpuesto>{MontoImpuesto}</dte:MontoImpuesto>
                            </dte:Impuesto>
                        """.format(
                            NombreCorto=tax_id.edxfel_sat_code,
                            CodigoUnidadGravable='1',
                            MontoGravable="{0:.2f}".format(round(line.price_subtotal,2)),
                            MontoImpuesto="{0:.2f}".format(round(amount,2))
                        )
                        tax_added = False
                        for tax_sum in taxes:
                            if tax_sum['NombreCorto'] == tax_id.edxfel_sat_code:
                                tax_added = True
                                tax_sum['Valor'] += round(amount,2)
                        if not tax_added:
                            taxes.append({
                                'NombreCorto': tax_id.edxfel_sat_code,
                                'Valor': "{0:.2f}".format(round(amount,2))
                            })
                if invoice.journal_id.edxfel_type not in ['NABN'] and line_taxes == 0:
                    excempt = True
                    xml_lines += """<dte:Impuesto>
                            <dte:NombreCorto>{NombreCorto}</dte:NombreCorto>
                            <dte:CodigoUnidadGravable>{CodigoUnidadGravable}</dte:CodigoUnidadGravable>
                            <dte:MontoGravable>{MontoGravable}</dte:MontoGravable>
                            <dte:MontoImpuesto>{MontoImpuesto}</dte:MontoImpuesto>o
                        </dte:Impuesto>
                    """.format(
                        NombreCorto='IVA',
                        CodigoUnidadGravable='2',
                        MontoGravable="{0:.2f}".format(round(line.price_subtotal,2)),
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
                """.format(TituloImpuestos='' if invoice.journal_id.edxfel_type in ['NABN'] else '</dte:Impuestos>',
                           Total="{0:.2f}".format(round(line_amount,2)))

            #
            # Frases
            #
            xml_phrases = ''
            if invoice.journal_id.edxfel_type not in ['NCRE', 'NDEB', 'NABN']:
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

            #
            # Encabezado del documento
            #
            sign_date = datetime.now().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('America/Guatemala'))

            sign_date_utc = datetime.now().replace(tzinfo=pytz.UTC)
            current_date = sign_date.strftime('%Y-%m-%dT%H:%M:%S-06:00')
            current_time = datetime.now().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('America/Guatemala')).strftime('%H:%M:%S-06:00')

            # invoice_sign_date = invoice.date_invoice + current_time
            invoice_sign_date = invoice.date_invoice.strftime('%Y-%m-%dT') + current_time
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
                        <dte:Receptor CorreoReceptor="{CorreoReceptor}" IDReceptor="{NITReceptor}" NombreReceptor="{NombreReceptor}">
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
                Tipo=invoice.journal_id.edxfel_type,
                AfiliacionIVA=self.vat_affiliation,
                CodigoEstablecimiento=invoice.journal_id.edxfel_establishment_code,
                CorreoEmisor=invoice.company_id.email if invoice.company_id.email else '',
                NITEmisor=invoice.company_id.vat.replace('-', '') if invoice.company_id.vat else 'C/F',
                NombreComercial=escape_string(invoice.journal_id.edxfel_comercial_name),
                NombreEmisor=escape_string(invoice.company_id.name),
                DireccionEmisor=escape_string(invoice.journal_id.edxfel_establishment_street),
                CodigoPostalEmisor=invoice.company_id.zip if invoice.company_id.zip else '01001',
                MunicipioEmisor=escape_string(invoice.company_id.city if invoice.company_id.city else ''),
                DepartamentoEmisor=escape_string(invoice.company_id.state_id.name if invoice.company_id.state_id else ''),
                PaisEmisor=escape_string(invoice.company_id.country_id.code if invoice.company_id.country_id else ''),
                DireccionReceptor=escape_string((invoice.partner_id.street if invoice.partner_id.street else '') + (' ' + invoice.partner_id.street2 if invoice.partner_id.street2 else '')),
                CorreoReceptor=invoice.partner_id.email if invoice.partner_id.email else '',
                NITReceptor=invoice.partner_id.vat.replace('-', '') if invoice.partner_id.vat else 'CF',
                NombreReceptor=escape_string(invoice.partner_id.name),
                CodigoPostal=invoice.partner_id.zip if invoice.partner_id.zip else '01001',
                Municipio=escape_string(invoice.partner_id.city if invoice.partner_id.city else ''),
                Departamento=escape_string(invoice.partner_id.state_id.name if invoice.partner_id.state_id else ''),
                Pais=escape_string(invoice.partner_id.country_id.code if invoice.partner_id.country_id else ''),
                Frases=xml_phrases,
                Items=xml_lines,
                TituloImpuestos='' if invoice.journal_id.edxfel_type in ['NABN'] else '<dte:TotalImpuestos>'
            )
            # xml += """</dte:Items>
            #                 <dte:Totales>
            #                 <dte:TotalImpuestos>
            # """
            if not invoice.journal_id.edxfel_type in ['NABN']:
                for tax in taxes:
                    xml += '<dte:TotalImpuesto NombreCorto="{NombreCorto}" TotalMontoImpuesto="{TotalMontoImpuesto}"/>'.format(
                        NombreCorto=tax['NombreCorto'],
                        TotalMontoImpuesto="{0:.2f}".format(round( float(tax['Valor']),2))
                    )

            extras = ''
            if invoice.journal_id.edxfel_type == 'FCAM':
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
            elif invoice.journal_id.edxfel_type in ['NCRE', 'NDEB']:
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
                    if invoice.refund_invoice_id.edxfel_sat_uuid:
                        id_complemento = 'ReferenciasNota'
                        nombre_complemento = 'ReferenciasNota'
                        original_document = invoice.refund_invoice_id.edxfel_sat_uuid
                        reason = 'MotivoAjuste="{}"'.format(invoice.name)
                    else:
                        id_complemento = 'ComplementoReferenciaNota'
                        nombre_complemento = 'Complemento Referencia Nota'
                        previous_regime = 'RegimenAntiguo="Antiguo"'
                        #                            original_document = invoice.refund_invoice_id.journal_id.edxfel_previous_authorization
                        original_document = invoice.refund_invoice_id.resolution_id.name
                        #                            reason = 'SerieDocumentoOrigen="{}" NumeroDocumentoOrigen="{}"'.format(invoice.refund_invoice_id.journal_id.edxfel_previous_serial, invoice.refund_invoice_id.name)
                        reason = 'SerieDocumentoOrigen="{}" NumeroDocumentoOrigen="{}"'.format(
                            invoice.refund_invoice_id.gface_dte_serial[8:9],
                            str(int(invoice.refund_invoice_id.gface_dte_number[16:100])))

                    references = references.format(
                        RegimenAnterior=previous_regime,
                        DocumentoOrigen=original_document,
                        FechaEmision=invoice.refund_invoice_id.date_invoice,
                        MotivoAjuste=reason,
                    )
                else:
                    id_complemento = 'ComplementoReferenciaNota'
                    nombre_complemento = 'Complemento Referencia Nota'
                    #                        reason = 'SerieDocumentoOrigen="{}" NumeroDocumentoOrigen="{}"'.format(invoice.journal_id.edxfel_previous_serial, invoice.name)
                    reason = 'SerieDocumentoOrigen="{}" NumeroDocumentoOrigen="{}"'.format(
                        invoice.refund_invoice_id.gface_dte_serial, invoice.refund_invoice_id.resolution_id.name)
                    references = references.format(
                        RegimenAnterior='RegimenAntiguo="Antiguo"',
                        DocumentoOrigen=invoice.journal_id.edxfel_previous_authorization,
                        FechaEmision=invoice.date_invoice,
                        MotivoAjuste=reason,
                    )
                extras = extras.format(
                    IDComplemento=id_complemento,
                    NombreComplemento=nombre_complemento,
                    Referencias=references
                )

            xml += """{TituloImpuestos}
                            <dte:GranTotal>{GranTotal}</dte:GranTotal>
                            </dte:Totales>{Complementos}
                        </dte:DatosEmision>
                    </dte:DTE>
                </dte:SAT>
</dte:GTDocumento>""".format(
                TituloImpuestos='' if invoice.journal_id.edxfel_type in ['NABN'] else '</dte:TotalImpuestos>',
                GranTotal="{0:.2f}".format(round(invoice.amount_total,2)), Complementos=extras)
            source_xml = xml
            print(xml)

            xmlb64 = ''
            sign_document = False
            if self.signing_type == 'LOCAL':
                tmp_dir = gettempdir()
                source_xml_file = os.path.join(tmp_dir, '{}_source.xml'.format(invoice.edxfel_uuid))
                signed_xml_file = os.path.join(tmp_dir, '{}.xml'.format(invoice.edxfel_uuid))
                with open(source_xml_file, 'w', encoding="utf-8") as xml_file:
                    xml_file.write(xml)
                # os.system('java -jar {} {} {} {} {}'.format('/Users/oscar/Desarrollo/java/Xadesedxfel.jar', source_xml_file, '/tmp/39796558-28d66a63138ff444.pfx', "'Neo2018$1'", invoice.edxfel_uuid))
                os.system("java -jar {} {} {} '{}' {} {} {}".format(self.signer_location, source_xml_file,
                                                                    self.certificate_file, self.certificate_password,
                                                                    invoice.edxfel_uuid, tmp_dir, 'DatosEmision'))

                if os.path.isfile(signed_xml_file):
                    with open(signed_xml_file, 'r') as myfile:
                        xml = myfile.read()
                    sign_document = True
                else:
                    raise UserError(_('edxfel: Signed XML file not found'))
            else:

                headers = {"Content-Type": "application/x-www-form-urlencoded"}

#                xml_request = """<?xml version="1.0" encoding="utf-8"?><soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"><soap12:Body><ConvertSignDocument xmlns="http://tempuri.org/"><Area>{_area}</Area><Password>{_password}</Password><DocumentType>{_type}</DocumentType><DocumentContent>{_xml}</DocumentContent></ConvertSignDocument></soap12:Body></soap12:Envelope>""".format(
#                    _area='FELFELPR', _password='administrador',_type='FACT', _xml=xml, _connector='Xslt' )


                response = requests.post(self.ws_url_document,  data=data, headers=headers)
                responseText = xmltodict.parse(response.text)
                resultado = responseText['soap:Envelope']['soap:Body']['ConvertSignDocumentResponse']['ConvertSignDocumentResult']
                print(resultado)


                data = {
                    'Area': 'FELFELPR',
                    'Password': 'administrador',
                    'DocumentType':  'FACT',
                    'DocumentContent':    base64.b64encode(xml.encode('utf-8')).decode('utf-8'),
                }
                print(xml)
                sign_response = requests.post(url=self.ws_url_signer, json=data)
                print("miguel")
                result = json.loads(sign_response.text)
                if result['resultado']:
                    xmlb64 = result['archivo']
                    xml = base64.b64decode(xmlb64).decode('utf-8')
                    sign_document = True
                else:
                    raise UserError(_('Error signing document: {}').format(result['descripcion']))

            if sign_document:
                headers = {
                    'usuario': self.certification_key,
                    'llave': self.user,
                    'identificador': invoice.edxfel_uuid,
                    'Content-Type': 'application/json',
                }
                data = {
                    'nit_emisor': invoice.company_id.vat.replace('-', '') if invoice.company_id.vat else 'C/F',
                    'correo_copia': 'ORamirezO@gmail.com',
                    'xml_dte': xmlb64
                }
                try:
                    response = requests.post(self.ws_url_document, headers=headers, data=json.dumps(data))
                    if response.ok:
                        result = json.loads(response.text)
                        if result['resultado']:

                            _sat_uuid = str(result['uuid']).split('-')
                            _mpfel_number = ''
                            _mpfel_serial = ''
                            _count = 0
                            for a in _sat_uuid:
                                if _count == 0:
                                    _mpfel_serial = a
                                if _count == 1 or _count == 2:
                                    _mpfel_number += a
                                _count += 1


                            invoice.write({
                                'edxfel_sign_date': invoice_sign_date,
                                'edxfel_sat_uuid': result['uuid'],
                                'edxfel_source_xml': source_xml,
                                'edxfel_signed_xml': xml,
                                'edxfel_result_xml': result['xml_certificado'],

                                'edx_serial': _mpfel_serial,
                                'edx_number': str(int(_mpfel_number, 16)),
                                'number': _mpfel_serial + '-' + str(int(_mpfel_number, 16)),
                                'move_name': _mpfel_serial + '-' + str(int(_mpfel_number, 16)),
                            })
                            _pos_id = self.env['ir.config_parameter'].search([('key', '=', 'pos')]).ids[0]
                            _tiene_pos = self.env['ir.config_parameter'].browse([_pos_id])
                            if _tiene_pos.value == 'True':
                                _order_id_ = self.env['pos.order'].search([('invoice_id', '=', invoice.id)])
                                if _order_id_:
                                    _order_id = self.env['pos.order'].search([('invoice_id', '=', invoice.id)]).ids[0]
                                    _pos_order_id  = self.env['pos.order'].browse([_order_id])
                                    _edxfel_comercial_name = invoice.journal_id.edxfel_comercial_name
                                    _serie_venta = _mpfel_serial  #invoice.journal_id.serie_venta
                                    _edxfel_establishment_street = invoice.journal_id.edxfel_establishment_street
                                    _edx_number = str(int(_mpfel_number, 16))
                                    _edxfel_sat_uuid = result['uuid']
                                    _edxfel_sign_date = invoice_sign_date

                                    _nit_empresa = invoice.company_id.vat
                                    _nombre_empresa = invoice.company_id.name

                                    _nombre_cliente = invoice.partner_id.name
                                    _nit = invoice.partner_id.vat
                                    _direccion_cliente = invoice.partner_id.street
                                    _fecha_factura = invoice.date_invoice
                                    _forma_pago = _pos_order_id.statement_ids[0].journal_id.name
                                    _caja = _pos_order_id.config_id.name
                                    _vendedor = _pos_order_id.create_uid.name

                                    _nit_certificador = self.nit_certificador
                                    _nombre_certificador = self.nombre_certificador
                                    _frase_certificador = self.frase_certificador

                                    _pos_order_id.write({  'frase_certificador':_frase_certificador,  'nombre_certificador':_nombre_certificador,  'nit_certificador':_nit_certificador,      'vendedor':_vendedor,           'caja':_caja,    'forma_pago':_forma_pago,        'fecha_factura':_fecha_factura,       'direccion_cliente':_direccion_cliente,           'nit':_nit,   'nombre_cliente' :_nombre_cliente,              'edxfel_sat_uuid':_edxfel_sat_uuid, 'edxfel_sign_date':_edxfel_sign_date   , 'edx_number':_edx_number,'nombre_empresa':_nombre_empresa, 'nit_empresa':_nit_empresa, 'edxfel_comercial_name':_edxfel_comercial_name,'serie_venta':_serie_venta,'edxfel_establishment_street':_edxfel_establishment_street })

                                    print('miguel')
                        else:
                            error_message = u''
                            if type(result['descripcion_errores']) is list:
                                for message in result['descripcion_errores']:
                                    error_message += '\n{}: {}'.format(message['fuente'], message['mensaje_error'])
                            else:
                                error_message += '\n{}: {}'.format(
                                    result['RegistraDocumentoXMLResponse']['listado_errores']['error']['cod_error'],
                                    result['RegistraDocumentoXMLResponse']['listado_errores']['error']['desc_error'])
                            raise UserError(error_message)
                    else:
                        raise UserError(
                            _('edxfel: Response error consuming web service: {}').format(str(response.text)))
                except Exception as e:
                    error_message = ''
                    if hasattr(e, 'object'):
                        if hasattr(e, 'reason'):
                            error_message = u"{}: {}".format(e.reason, e.object)
                        else:
                            error_message = u" {}".format(e.object)
                    elif hasattr(e, 'message'):
                        error_message = e.message
                    elif hasattr(e, 'name'):
                        error_message = e.name
                    else:
                        error_message = e
                    raise UserError(_('edxfel: Error consuming web service: {}').format(error_message))
            else:
                raise UserError(_('edxfel Signer: {}').format(result['message']))


    def void_document(self, invoice):
        token = None
        if not invoice.journal_id.edxfel_type:
            return
        elif invoice.journal_id.edxfel_type == '':
            return
        elif not invoice.date_invoice:
            raise UserError(_('Missing document date'))
        else:
            if not invoice.edxfel_void_uuid:
                invoice.edxfel_void_uuid = str(uuid.uuid4())

            # current_date = datetime.now().replace(tzinfo=pytz.utc).astimezone(pytz.timezone(self.env.user.tz))
            sign_date = datetime.now().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('America/Guatemala'))
#            sign_date = datetime.now().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone(self.env.user.tz))

            sign_date_utc = datetime.now().replace(tzinfo=pytz.UTC)
            current_date = sign_date.strftime('%Y-%m-%dT%H:%M:%S-06:00')
            current_time = datetime.now().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('America/Guatemala')).strftime('%H:%M:%S-06:00')
#            current_time = datetime.now().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone(self.env.user.tz)).strftime('%H:%M:%S-06:00')

            invoice_sign_date = invoice.edxfel_sign_date.strftime('%Y-%m-%dT%H:%M:%S-06:00')
            void_sign_date = invoice.date_invoice.strftime('%Y-%m-%dT') + current_time

            xml = """<?xml version="1.0" encoding="UTF-8"?><dte:GTAnulacionDocumento Version="0.1" xmlns:dte="http://www.sat.gob.gt/dte/fel/0.1.0" xmlns:xd="http://www.w3.org/2000/09/xmldsig#" xmlns:n1="http://www.altova.com/samplexml/other-namespace" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <dte:SAT>
                    <dte:AnulacionDTE ID="DatosCertificados">
                        <dte:DatosGenerales ID="DatosAnulacion"
                            NumeroDocumentoAAnular="{NumeroDocumentoAAnular}"
                            NITEmisor="{NITEmisor}"
                            IDReceptor="{IDReceptor}"
                            FechaEmisionDocumentoAnular="{FechaEmisionDocumentoAnular}"
                            FechaHoraAnulacion="{FechaHoraAnulacion}"
                            MotivoAnulacion="Cancelacion"
                        />
                    </dte:AnulacionDTE>
                </dte:SAT></dte:GTAnulacionDocumento>""".format(
                NumeroDocumentoAAnular=invoice.edxfel_sat_uuid,
                NITEmisor=invoice.company_id.vat.replace('-', '') if invoice.company_id.vat else 'C/F',
                IDReceptor=invoice.partner_id.vat.replace('-', '') if invoice.partner_id.vat else 'CF',
                FechaEmisionDocumentoAnular=invoice_sign_date,
                FechaHoraAnulacion=void_sign_date,
                NITCertificador=invoice.company_id.vat.replace('-', '') if invoice.company_id.vat else 'C/F',
                NombreCertificador=invoice.company_id.name,
                FechaHoraCertificacion=void_sign_date,
            )

            source_xml = xml

            # tmp_dir = gettempdir()
            # source_xml_file = os.path.join(tmp_dir, '{}_source.xml'.format(invoice.edxfel_void_uuid))
            # signed_xml_file = os.path.join(tmp_dir, '{}.xml'.format(invoice.edxfel_void_uuid))
            # with open(source_xml_file, 'w') as xml_file:
            #     xml_file.write(xml)
            # os.system("java -jar {} {} {} '{}' {} {} {}".format(self.signer_location, source_xml_file, self.certificate_file, self.certificate_password, invoice.edxfel_void_uuid, tmp_dir, 'DatosGenerales'))
            #
            # if not os.path.isfile(signed_xml_file):
            #     raise UserError(_('edxfel: Signed XML file not found'))
            # elif self.token:
            sign_document = False
            if self.signing_type == 'LOCAL':
                tmp_dir = gettempdir()
                source_xml_file = os.path.join(tmp_dir, '{}_source.xml'.format(invoice.edxfel_void_uuid))
                signed_xml_file = os.path.join(tmp_dir, '{}.xml'.format(invoice.edxfel_void_uuid))
                with open(source_xml_file, 'w') as xml_file:
                    xml_file.write(xml)
                # os.system('java -jar {} {} {} {} {}'.format('/Users/oscar/Desarrollo/java/Xadesedxfel.jar', source_xml_file, '/tmp/39796558-28d66a63138ff444.pfx', "'Neo2018$1'", invoice.edxfel_uuid))
                os.system("java -jar {} {} {} '{}' {} {} {}".format(self.signer_location, source_xml_file,
                                                                    self.certificate_file, self.certificate_password,
                                                                    invoice.edxfel_void_uuid, tmp_dir,
                                                                    'DatosGenerales'))

                if os.path.isfile(signed_xml_file):
                    with open(signed_xml_file, 'r') as myfile:
                        xml = myfile.read()
                    sign_document = True
                else:
                    raise UserError(_('edxfel: Signed XML file not found'))
            else:

                data = {
                    'llave': self.sign_key,
                    'archivo': base64.b64encode(xml.encode('utf-8')).decode('utf-8'),
                    'codigo': '1001',#invoice.edxfel_void_uuid,
                    'alias': self.sign_user,
                    "es_anulacion": 'S'
                }
                sign_response = requests.post(url=self.ws_url_signer, json=data)
                result = json.loads(sign_response.text)
                if result['resultado']:
                    xmlb64 = result['archivo']
                    xml = base64.b64decode(xmlb64).decode('utf-8')
                    sign_document = True
                else:
                    raise UserError(_('Error signing document: {}').format(result['descripcion']))

            if sign_document:

                headers = {
                    'usuario': self.certification_key,
                    'llave':  self.user,
                    'identificador': invoice.edxfel_void_uuid,
                    'Content-Type': 'application/json',
                }
                data = {
                    'nit_emisor': invoice.company_id.vat.replace('-', '') if invoice.company_id.vat else 'C/F',
                    'correo_copia': 'ORamirezO@gmail.com',
                    'xml_dte': xmlb64
                }
                # data = '<?xml version="1.0" encoding="UTF-8" standalone="no"?><AnulaDocumentoXMLRequest id="{}"><xml_dte><![CDATA[{}]]></xml_dte></AnulaDocumentoXMLRequest>'.format(
                #     invoice.edxfel_void_uuid.upper(), xml)
                try:
                    response = requests.post(self.ws_url_void, headers=headers, data=json.dumps(data))
                    if response.ok:
                        result = json.loads(response.text)
                        if result['resultado']:
                            invoice.write({
                                'edxfel_void_sat_uuid': result['uuid'],
                                'edxfel_void_source_xml': source_xml,
                                'edxfel_void_signed_xml': xml,
                                'edxfel_void_result_xml': result['xml_certificado'],
                            })
                            invoice.action_invoice_cancel()
                        else:
                            error_message = u''
                            if type(result['descripcion_errores']) is list:
                                for message in result['descripcion_errores']:
                                    error_message += '\n{}: {}'.format(message['fuente'], message['mensaje_error'])
                            else:
                                error_message += '\n{}: {}'.format(
                                    result['RegistraDocumentoXMLResponse']['listado_errores']['error']['cod_error'],
                                    result['RegistraDocumentoXMLResponse']['listado_errores']['error'][
                                        'desc_error'])
                            raise UserError(error_message)
                    else:
                        raise UserError(
                            _('edxfel: Response error consuming web service: {}').format(str(response.text)))

                except Exception as e:
                    error_message = ''
                    if hasattr(e, 'object'):
                        if hasattr(e, 'reason'):
                            error_message = u"{}: {}".format(e.reason, e.object)
                        else:
                            error_message = u" {}".format(e.object)
                    elif hasattr(e, 'message'):
                        error_message = e.message
                    elif hasattr(e, 'name'):
                        error_message = e.name
                    else:
                        error_message = e
                    raise UserError(_('edxfel: Error consuming web service: {}').format(error_message))
            else:
                raise UserError(_('edxfel: API key not set'))
