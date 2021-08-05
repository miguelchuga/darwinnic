# -*- coding: utf-8 -*-
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


# xml="""<?xml version="1.0" encoding="UTF-8"?><dte:GTDocumento Version="0.4" xmlns:dte="http://www.sat.gob.gt/dte/fel/0.1.0" xmlns:xd="http://www.w3.org/2000/09/xmldsig#"><dte:SAT ClaseDocumento="dte"><dte:DTE ID="DatosCertificados"><dte:DatosEmision ID="DatosEmision"><dte:DatosGenerales CodigoMoneda="GTQ"  FechaHoraEmision="2020-03-13T07:50:43-06:00"  Tipo="FACT"/><dte:Emisor AfiliacionIVA="GEN" CodigoEstablecimiento="pruebas estabilshment" CorreoEmisor="admin@organica.net" NITEmisor="58903119" NombreComercial="pruebas comercial name" NombreEmisor="ALIMENTOS ORGANICOS SOCIEDAD ANONIMA"><dte:DireccionEmisor><dte:Direccion>pruebas stablisment stres</dte:Direccion><dte:CodigoPostal>01011</dte:CodigoPostal><dte:Municipio>Guatemala</dte:Municipio><dte:Departamento>Guatemala</dte:Departamento><dte:Pais>GT</dte:Pais></dte:DireccionEmisor></dte:Emisor><dte:Receptor CorreoReceptor="espacioculinariogt@yahoo.com" IDReceptor="6923569" NombreReceptor="Oscar de Leon"><dte:DireccionReceptor><dte:Direccion>Ciudad Guatemala</dte:Direccion><dte:CodigoPostal>01011</dte:CodigoPostal><dte:Municipio>Guatemala</dte:Municipio><dte:Departamento>Guatemala</dte:Departamento><dte:Pais>GT</dte:Pais></dte:DireccionReceptor></dte:Receptor><dte:Frases><dte:Frase CodigoEscenario="1" TipoFrase="1" /><dte:Frase CodigoEscenario="1" TipoFrase="2" /></dte:Frases><dte:Items><dte:Item BienOServicio="B" NumeroLinea="1"><dte:Cantidad>10.0</dte:Cantidad><dte:UnidadMedida>lib</dte:UnidadMedida><dte:Descripcion>Filete de pechuga de pollo libra</dte:Descripcion><dte:PrecioUnitario>1.0</dte:PrecioUnitario><dte:Precio>10.00</dte:Precio><dte:Descuento>0.00</dte:Descuento><dte:Impuestos><dte:Impuesto><dte:NombreCorto>IVA</dte:NombreCorto><dte:CodigoUnidadGravable>1</dte:CodigoUnidadGravable><dte:MontoGravable>8.93</dte:MontoGravable><dte:MontoImpuesto>1.07</dte:MontoImpuesto></dte:Impuesto></dte:Impuestos><dte:Total>10.00</dte:Total></dte:Item></dte:Items><dte:Totales><dte:TotalImpuestos><dte:TotalImpuesto NombreCorto="IVA" TotalMontoImpuesto="1.07"/></dte:TotalImpuestos><dte:GranTotal>10.00</dte:GranTotal></dte:Totales></dte:DatosEmision></dte:DTE></dte:SAT></dte:GTDocumento>"""
xml = """<?xml version="1.0" encoding="UTF-8"?>
<dte:GTDocumento Version="0.4" xmlns:dte="http://www.sat.gob.gt/dte/fel/0.1.0" xmlns:xd="http://www.w3.org/2000/09/xmldsig#">
    <dte:SAT ClaseDocumento="dte">
        <dte:DTE ID="DatosCertificados">
            <dte:DatosEmision ID="DatosEmision">
                <dte:DatosGenerales CodigoMoneda="GTQ" FechaHoraEmision="2020-04-22T07:50:43-06:00" Tipo="FACT" />
                <dte:Emisor AfiliacionIVA="GEN" CodigoEstablecimiento="pruebas estabilshment" CorreoEmisor="admin@organica.net" NITEmisor="58903119" NombreComercial="pruebas comercial name" NombreEmisor="ALIMENTOS ORGANICOS SOCIEDAD ANONIMA">
                    <dte:DireccionEmisor>
                        <dte:Direccion>pruebas stablisment stres</dte:Direccion>
                        <dte:CodigoPostal>01011</dte:CodigoPostal>
                        <dte:Municipio>Guatemala</dte:Municipio>
                        <dte:Departamento>Guatemala</dte:Departamento>
                        <dte:Pais>GT</dte:Pais>
                    </dte:DireccionEmisor>
                </dte:Emisor>
                <dte:Receptor CorreoReceptor="espacioculinariogt@yahoo.com" IDReceptor="6923569" NombreReceptor="Oscar de Leon">
                    <dte:DireccionReceptor>
                        <dte:Direccion>Ciudad Guatemala</dte:Direccion>
                        <dte:CodigoPostal>01011</dte:CodigoPostal>
                        <dte:Municipio>Guatemala</dte:Municipio>
                        <dte:Departamento>Guatemala</dte:Departamento>
                        <dte:Pais>GT</dte:Pais>
                    </dte:DireccionReceptor>
                </dte:Receptor>
                <dte:Frases>
                    <dte:Frase CodigoEscenario="1" TipoFrase="1" />
                    <dte:Frase CodigoEscenario="1" TipoFrase="2" />
                </dte:Frases>
                <dte:Items>
                    <dte:Item BienOServicio="B" NumeroLinea="1">
                        <dte:Cantidad>10.0</dte:Cantidad>
                        <dte:UnidadMedida>lib</dte:UnidadMedida>
                        <dte:Descripcion>Filete de pechuga de pollo libra</dte:Descripcion>
                        <dte:PrecioUnitario>1.0</dte:PrecioUnitario>
                        <dte:Precio>10.00</dte:Precio>
                        <dte:Descuento>0.00</dte:Descuento>
                        <dte:Impuestos>
                            <dte:Impuesto>
                                <dte:NombreCorto>IVA</dte:NombreCorto>
                                <dte:CodigoUnidadGravable>1</dte:CodigoUnidadGravable>
                                <dte:MontoGravable>8.93</dte:MontoGravable>
                                <dte:MontoImpuesto>1.07</dte:MontoImpuesto>
                            </dte:Impuesto>
                        </dte:Impuestos>
                        <dte:Total>10.00</dte:Total>
                    </dte:Item>
                </dte:Items>
                <dte:Totales>
                    <dte:TotalImpuestos>
                        <dte:TotalImpuesto NombreCorto="IVA" TotalMontoImpuesto="1.07" />
                    </dte:TotalImpuestos>
                    <dte:GranTotal>10.00</dte:GranTotal>
                </dte:Totales>
            </dte:DatosEmision>
        </dte:DTE>
    </dte:SAT>
</dte:GTDocumento>"""
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
}

data = {
    'Area': 'FELFELPR',
    'Password': 'administrador',
    'DocumentType': 'FACT',
    'DocumentContent': xml,
    'Connector': 'Xslt'
}
url = 'http://edxfeltest.southcentralus.cloudapp.azure.com/CertificacionPDF/Core.asmx?op=CreateDocumentWithCustomResponse'
response = requests.post(url, data=data, headers=headers)
result = html.unescape(response.text)
pos = result.find('<![CDATA[')
if pos >= 0:
    # pos = result.find('<DTECertified>', pos)
    # end = result.find('</DTECertified>', pos) + 15
    end = result.find(']]', pos)
    doc = html.unescape(result[pos+9:end]).replace('<?xml version="1.0"?>', '')
    dte = xmltodict.parse(doc)

print('edx')