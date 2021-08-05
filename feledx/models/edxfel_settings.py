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

import zeep

class edxfel_settings(models.Model):
    _name = "feledx.settings"
    _description = "Edx FEL settings"

    company_id = fields.Many2one('res.company', string='Empresa')
    ws_url_document = fields.Char('Document web service URL', default='https://')
    ws_timeout = fields.Integer('Web service timeout', default=300)
    user = fields.Char('Certification user')
    sign_area = fields.Char('Sign area')
    sign_connector = fields.Char('Sign connector')
    sign_convertdocument = fields.Boolean('Sign ConvertDocument')
    sign_signdocument = fields.Boolean('Sign SignDocument')
    sign_printdocument = fields.Boolean('Sign PrintDocument')
    sign_Password = fields.Char('Password')

    vat_affiliation = fields.Selection([
        ('GEN', 'GEN'),
        ('EXE', 'EXE'),
        ('PEQ', 'PEQ'),
    ], string='VAT affiliation', default='GEN')
    isr_scenery = fields.Char('ISR sceneries')
    isr_phrases = fields.Char('ISR phrases')
    excempt_scenery = fields.Char('Excempt scenery')
    descripcion_resolucion = fields.Char('Descripcion resolución')
    numero_resolucion = fields.Char('Número resolución')
    fecha_resolucion = fields.Char('Fecha resolución')


    def sign_document(self, invoice):
        def escape_string(value):
            if not value:
                value = ''
            return html.escape(value).encode("ascii", "xmlcharrefreplace").decode('utf8')

        token = None
        if not invoice.journal_id.edxfel_type:
            return
        elif invoice.journal_id.edxfel_type == '':
            return
        elif invoice.edxfel_void_signed_xml:
            return
        elif invoice.edxfel_uuid:
            return

        elif not invoice.invoice_date:
            raise UserError(_('Missing document date'))
        else:
            parter_vat = invoice.partner_id.vat.replace('-', '') if invoice.partner_id.vat else 'CF'
            partner_name = escape_string(invoice.partner_id.name)

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
                    line_gross = round(line.price_unit * line.quantity, 2) #line.price_subtotal
                    line_discount = line_gross-line.price_subtotal   #round(line_gross * line.discount / 100, 2)
                    line_amount = line.price_subtotal #line_gross - line_discount

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
                    UnidadMedida=escape_string(line.product_uom_id.name)[:3],
                    Descripcion=escape_string(line.name),
                    PrecioUnitario=round(line.price_unit,2),
                    Precio="{0:.2f}".format(round(line_gross,2)),
                    Descuento="{0:.2f}".format(round(line_discount,2)),
                    TituloImpuestos='' if invoice.journal_id.edxfel_type in ['NABN'] else '<dte:Impuestos>'
                )
                # UnidadMedida = escape_string(line.uom_id.name[:3]),

                line_taxes = 0
                if invoice.journal_id.edxfel_type not in ['NABN']:
                    for tax_id in line.tax_ids:
                        amount = 0
                        if invoice.journal_id.edxfel_type not in ['NABN'] and tax_id.amount_type == 'percent' and tax_id.edxfel_sat_code == 'IVA':
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
                                if tax_sum['Valor']:
                                    tax_sum['Valor'] += round(amount,2)
                        if not tax_added:
                            taxes.append({
                                'NombreCorto': tax_id.edxfel_sat_code,
                                'Valor':round(amount,2)
                                #                                'Valor': "{0:.2f}".format(round(amount,2))
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

            if excempt:
                xml_phrases += self.excempt_scenery
            else:
                xml_phrases = self.isr_phrases
            if invoice.journal_id.edxfel_type in ['NCRE', 'NDEB']:
                xml_phrases = ''

            #
            # Encabezado del documento
            #
            sign_date = datetime.now().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('America/Guatemala'))

            current_time = sign_date.strftime('T%H:%M:%S-06:00')
            invoice_sign_date = invoice.date_invoice + current_time #str(invoice.invoice_date) + current_time

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
                            </dte:Complementos>""".format(FechaVencimiento=invoice.invoice_date_due, Monto=invoice.amount_total)
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
                if invoice.reversed_entry_id:
                    previous_regime = ''
                    original_document = invoice.reversed_entry_id.name
                    reason = ''
                    if invoice.reversed_entry_id.edxfel_uuid:
                        id_complemento = 'ReferenciasNota'
                        nombre_complemento = 'ReferenciasNota'
                        original_document = invoice.reversed_entry_id.edxfel_uuid
                        reason = 'MotivoAjuste="{}"'.format(invoice.ref)
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
                        FechaEmision=invoice.reversed_entry_id.invoice_date,
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
            """.format(
                TituloImpuestos='' if invoice.journal_id.edxfel_type in ['NABN'] else '</dte:TotalImpuestos>',
                GranTotal="{0:.2f}".format(round(invoice.amount_total,2)), Complementos=extras)



            dir_entrega=''
            city_entrega=''
            country_entrega=''
            name_entrega=''
            for _ids  in invoice.partner_id.child_ids:
                if _ids.type == 'delivery':
                    dir_entrega = _ids.contact_address_complete
                    city_entrega = _ids.city
                    country_entrega = _ids.country_id.name
                    name_entrega = _ids.name



            xml +=""""
                        <dte:Personalizado>
                            <dte:Personalizado1> {descripcion_resolucion} </dte:Personalizado1>
                            <dte:Personalizado2> {numero_resolucion} </dte:Personalizado2>
                            <dte:Personalizado3> {fecha_resolucion} </dte:Personalizado3>
                            <dte:Personalizado4> {x_gira} </dte:Personalizado4>
                            <dte:Personalizado5> {x_codigo_interno} </dte:Personalizado5>
                            <dte:Personalizado6> {street} </dte:Personalizado6>
                            <dte:Personalizado7> {city} </dte:Personalizado7>
                            <dte:Personalizado8> {country} </dte:Personalizado8>
                            <dte:Personalizado9>  {x_codigo_vendedor} </dte:Personalizado9>
                            <dte:Personalizado10/>
                            <dte:Personalizado11/>
                            <dte:Personalizado12/>
                            <dte:Personalizado13/>
                            <dte:Personalizado14/>
                            <dte:Personalizado15/>
                        </dte:Personalizado>
                    </dte:SAT>
                </dte:GTDocumento>""".format(
                descripcion_resolucion=self.descripcion_resolucion,
                numero_resolucion=self.numero_resolucion,
                fecha_resolucion=self.fecha_resolucion,
                x_gira=invoice.partner_id.x_gira if invoice.partner_id.x_gira else '',
                x_codigo_interno=invoice.partner_id.x_codigo_interno if invoice.partner_id.x_codigo_interno else '',
                street=dir_entrega if dir_entrega else '',
                city=city_entrega if city_entrega else '',
                country=country_entrega if country_entrega else '',
                x_codigo_vendedor=invoice.partner_id.x_codigo_vendedor if invoice.partner_id.x_codigo_vendedor else '',

            )

            source_xml = xml
            print(xml)

            edx = self.search([('company_id', '=', self.env.company.id)])
            wsdl = edx.ws_url_document
            error = ''
            try:
                client = zeep.Client(wsdl=wsdl)
                result = client.service.CreateDocumentWithCustomResponse(Area=edx.sign_area,
                                                                     Password=edx.sign_Password,
                                                                     DocumentType=invoice.journal_id.edxfel_type,
                                                                     DocumentContent=xml,
                                                                     Connector=edx.sign_connector,
                                                                     ConvertDocument=edx.sign_convertdocument ,
                                                                     SignDocument=edx.sign_signdocument,
                                                                     PrintDocument=edx.sign_printdocument, )

                # si hay error
                pos = result.find('<HasError>')
                end = result.find('</HasError>', pos)
                error = html.unescape(result[pos + 10:end])

                if error == 'true':
                    dte_error = xmltodict.parse(html.unescape(result).replace('<?xml version="1.0"?>', ''))
                    _error = dte_error['ProcessResult']['Error']['Description']
                    raise UserError(_('MPFEL: Response error consuming web service: {}').format(_error))
                else:
                    pos = result.find('<![CDATA[')
                    if pos >= 0:
                        end = result.find(']]', pos)
                    doc = html.unescape(result[pos + 9:end]).replace('<?xml version="1.0"?>', '')
                    dte = xmltodict.parse(doc)
                    serie = dte['DTECertification']['DTECertified']['DTE']['dte:GTDocumento']['dte:SAT']['dte:DTE'][
                        'dte:Certificacion']['dte:NumeroAutorizacion']['@Serie']
                    numero = dte['DTECertification']['DTECertified']['DTE']['dte:GTDocumento']['dte:SAT']['dte:DTE'][
                        'dte:Certificacion']['dte:NumeroAutorizacion']['@Numero']
                    uuid = dte['DTECertification']['DTECertified']['AuthorizationNumber']
                    hora = dte['DTECertification']['DTECertified']['DTE']['dte:GTDocumento']['dte:SAT']['dte:DTE'][
                        'dte:Certificacion']['dte:FechaHoraCertificacion']
                    # PDF
                    pos = result.find('<Buffer>')
                    end = result.find('</Buffer>', pos)
                    pdf = html.unescape(result[pos + 8:end])



                    pos = xml.find('FechaHoraEmision')
                    emision = xml[pos+18 :pos+43]

                    # para el xml de anulacion lo deja preparado



                    invoice.write({
                        'edx_pdf': pdf,
                        'edx_file_name': uuid + '.' + 'pdf',
                        'edxfel_source_xml': xml,
                        'edxfel_signed_xml': doc,
                        'edxfel_sign_date': hora,
                        'edx_number': numero,
                        'edx_serial': serie,
                        'edxfel_uuid': uuid,
                        'edxfel_sign_date':emision,
                    })

            except Exception as e:
                error_message=''
                if error:
                    # si hay error
                    pos = result.find('<HasError>')
                    end = result.find('</HasError>', pos)
                    error = html.unescape(result[pos + 10:end])
                    if error == 'true':
                        dte_error = xmltodict.parse(html.unescape(result).replace('<?xml version="1.0"?>', ''))
                        error_message +=  dte_error['ProcessResult']['Error']['Description']

                raise UserError(_('MPFEL: Error consuming web service: {}').format(error_message))
                print('¡eso es todo amigos!')


########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################

    def void_document(self, invoice):
        def escape_string(value):
            if not value:
                value = ''
            return html.escape(value).encode("ascii", "xmlcharrefreplace").decode('utf8')

        token = None
        if not invoice.journal_id.edxfel_type:
            return
        elif invoice.journal_id.edxfel_type == '':
            return
        elif invoice.edxfel_void_signed_xml:
            return
        elif not invoice.invoice_date:
            raise UserError(_('Missing document date'))
        else:
            parter_vat = invoice.partner_id.vat.replace('-', '') if invoice.partner_id.vat else 'CF'
            partner_name = escape_string(invoice.partner_id.name)

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
#                    line_gross = line.price_subtotal
#                    line_discount = round(line_gross * line.discount / 100, 2)
#                    line_amount = line_gross - line_discount
                    line_gross = round(line.price_unit * line.quantity, 2) #line.price_subtotal
                    line_discount = line_gross-line.price_subtotal   #round(line_gross * line.discount / 100, 2)
                    line_amount = line.price_subtotal #line_gross - line_discount

                xml_lines += """<dte:Item BienOServicio="{BienOServicio}" NumeroLinea="{NumeroLinea}">
                         <dte:Cantidad>{Cantidad}</dte:Cantidad>
                         <dte:UnidadMedida>{UnidadMedida}</dte:UnidadMedida>
                         <dte:Descripcion>{Descripcion}</dte:Descripcion>
                         <dte:PrecioUnitario>{PrecioUnitario}</dte:PrecioUnitario>
                         <dte:Precio>{Precio}</dte:Precio>
                         <dte:Descuento>{Descuento}</dte:Descuento>{TituloImpuestos}""".format(
                    BienOServicio='S' if line.product_id.type == 'service' else 'B',
                    NumeroLinea=line_number,
                    Cantidad=round(line.quantity, 2),
                    UnidadMedida=escape_string(line.product_uom_id.name)[:3],
                    Descripcion=escape_string(line.name),
                    PrecioUnitario=round(line.price_unit, 2),
                    Precio="{0:.2f}".format(round(line_gross, 2)),
                    Descuento="{0:.2f}".format(round(line_discount, 2)),
                    TituloImpuestos='' if invoice.journal_id.edxfel_type in ['NABN'] else '<dte:Impuestos>'
                )

                line_taxes = 0
                if invoice.journal_id.edxfel_type not in ['NABN']:
                    for tax_id in line.tax_ids:
                        amount = 0
                        if invoice.journal_id.edxfel_type not in [
                            'NABN'] and tax_id.amount_type == 'percent' and tax_id.edxfel_sat_code == 'IVA':
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
                            MontoGravable="{0:.2f}".format(round(line.price_subtotal, 2)),
                            MontoImpuesto="{0:.2f}".format(round(amount, 2))
                        )
                        tax_added = False
                        for tax_sum in taxes:
                            if tax_sum['NombreCorto'] == tax_id.edxfel_sat_code:
                                tax_added = True
                                if tax_sum['Valor']:
                                    tax_sum['Valor'] += round(amount, 2)
                        if not tax_added:
                            taxes.append({
                                'NombreCorto': tax_id.edxfel_sat_code,
                                'Valor': round(amount, 2)
                                #                                'Valor': "{0:.2f}".format(round(amount,2))
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
                        MontoGravable="{0:.2f}".format(round(line.price_subtotal, 2)),
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
                            Total="{0:.2f}".format(round(line_amount, 2)))

            #
            # Frases
            #
            xml_phrases = ''


#            if invoice.journal_id.edxfel_type not in ['NCRE', 'NDEB', 'NABN']:
#                xml_phrases = self.isr_phrases
            if excempt:
                xml_phrases += self.excempt_scenery
            else:
                xml_phrases = self.isr_phrases

            xml_phrases = ''
            #
            # Encabezado del documento
            #
            sign_date = datetime.now().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('America/Guatemala'))

            current_time = sign_date.strftime('T%H:%M:%S-06:00')
            invoice_sign_date = str(invoice.invoice_date) + current_time

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
                Tipo='ANUL',
                AfiliacionIVA=self.vat_affiliation,
                CodigoEstablecimiento=invoice.journal_id.edxfel_establishment_code,
                CorreoEmisor=invoice.company_id.email if invoice.company_id.email else '',
                NITEmisor=invoice.company_id.vat.replace('-', '') if invoice.company_id.vat else 'C/F',
                NombreComercial=escape_string(invoice.journal_id.edxfel_comercial_name),
                NombreEmisor=escape_string(invoice.company_id.name),
                DireccionEmisor=escape_string(invoice.journal_id.edxfel_establishment_street),
                CodigoPostalEmisor=invoice.company_id.zip if invoice.company_id.zip else '01001',
                MunicipioEmisor=escape_string(invoice.company_id.city if invoice.company_id.city else ''),
                DepartamentoEmisor=escape_string(
                    invoice.company_id.state_id.name if invoice.company_id.state_id else ''),
                PaisEmisor=escape_string(invoice.company_id.country_id.code if invoice.company_id.country_id else ''),
                DireccionReceptor=escape_string((invoice.partner_id.street if invoice.partner_id.street else '') + (
                    ' ' + invoice.partner_id.street2 if invoice.partner_id.street2 else '')),
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


            xml_anula = """<dte:Complementos>
                    <dte:AnulacionDTE ID="DatosCertificados">
                        <dte:DatosGenerales ID="DatosAnulacion"
                                NumeroDocumentoAAnular="{documento}"
                                FechaEmisionDocumentoAnular="{fecha}"
                                MotivoAnulacion="ANULACION"/>
                    </dte:AnulacionDTE>
                </dte:Complementos>""".format(documento=invoice.edxfel_uuid, fecha=invoice.edxfel_sign_date)

            xml += """{TituloImpuestos}
                                     <dte:GranTotal>{GranTotal}</dte:GranTotal>
                                     </dte:Totales> 
                                    {Anulacion}
                                 </dte:DatosEmision>
                             </dte:DTE>
                           </dte:SAT>
                         </dte:GTDocumento>
                     """.format(
                TituloImpuestos='</dte:TotalImpuestos>',
                Anulacion=xml_anula,
                GranTotal="{0:.2f}".format(round(invoice.amount_total, 2)))




            source_xml = xml
            print(xml)





            edx = self.search([('company_id', '=', self.env.company.id)])
            wsdl = edx.ws_url_document
            error = ''
            try:
                client = zeep.Client(wsdl=wsdl)
                result = client.service.CreateDocumentWithCustomResponse(Area=edx.sign_area,
                                                                         Password=edx.sign_Password,
                                                                         DocumentType='ANUL',
                                                                         DocumentContent=xml,
                                                                         Connector=edx.sign_connector,
                                                                         ConvertDocument=edx.sign_convertdocument,
                                                                         SignDocument=edx.sign_signdocument,
                                                                         PrintDocument=edx.sign_printdocument, )

                # si hay error
                pos = result.find('<HasError>')
                end = result.find('</HasError>', pos)
                error = html.unescape(result[pos + 10:end])

                if error == 'true':
                    dte_error = xmltodict.parse(html.unescape(result).replace('<?xml version="1.0"?>', ''))
                    _error = dte_error['ProcessResult']['Error']['Description']
                    raise UserError(_('MPFEL: Response error consuming web service: {}').format(_error))
                else:
                    pos = result.find('<![CDATA[')
                    if pos >= 0:
                        end = result.find(']]', pos)
                    doc = html.unescape(result[pos + 9:end]).replace('<?xml version="1.0"?>', '')
                    print(doc)
#                    dte = xmltodict.parse(doc)
#                    serie = dte['DTECertification']['DTECertified']['DTE']['dte:GTDocumento']['dte:SAT']['dte:DTE'][
#                        'dte:Certificacion']['dte:NumeroAutorizacion']['@Serie']
#                    numero = dte['DTECertification']['DTECertified']['DTE']['dte:GTDocumento']['dte:SAT']['dte:DTE'][
#                        'dte:Certificacion']['dte:NumeroAutorizacion']['@Numero']
#                    uuid = dte['DTECertification']['DTECertified']['AuthorizationNumber']
#                    hora = dte['DTECertification']['DTECertified']['DTE']['dte:GTDocumento']['dte:SAT']['dte:DTE'][
#                        'dte:Certificacion']['dte:FechaHoraCertificacion']
#                    # PDF
#                    pos = result.find('<Buffer>')
#                    end = result.find('</Buffer>', pos)
#                    pdf = html.unescape(result[pos + 8:end])


                    # para el xml de anulacion lo deja preparado



                    invoice.write({
                        'edxfel_void_signed_xml': doc,
#                        'edxfel_void_sat_uuid': uuid,
                        'edxfel_void_source_xml': xml,
                    })
                    invoice.button_cancel()


            except Exception as e:
                error_message = ''
                if error:
                    # si hay error
                    pos = result.find('<HasError>')
                    end = result.find('</HasError>', pos)
                    error = html.unescape(result[pos + 10:end])
                    if error == 'true':
                        dte_error = xmltodict.parse(html.unescape(result).replace('<?xml version="1.0"?>', ''))
                        error_message += dte_error['ProcessResult']['Error']['Description']

                raise UserError(_('MPFEL: Error consuming web service: {}').format(error_message))
                print('¡eso es todo amigos!')
