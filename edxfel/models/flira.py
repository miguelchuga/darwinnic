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


from suds.client import Client
from suds.xsd.doctor import Import, ImportDoctor


from suds.client import Client
from suds.xsd.doctor import Import, ImportDoctor



xml = """ <?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
   <soapenv:Header/>
   <soapenv:Body>
      <tem:CreateDocumentWithCustomResponse>
         <!--Optional:-->
         <tem:Area>FELODOO</tem:Area>
         <!--Optional:-->
         <tem:Password>administrador</tem:Password>
         <!--Optional:-->
         <tem:DocumentType>FACT</tem:DocumentType>
         <!--Optional:-->
         <tem:DocumentContent><![CDATA[<?xml version="1.0" encoding="utf-8"?>
      <dte:GTDocumento xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:cfc="http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0" xmlns:cno="http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:cex="http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0" xmlns:cfe="http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0" Version="0.4" xmlns:dte="http://www.sat.gob.gt/dte/fel/0.1.0">
        <dte:SAT ClaseDocumento="dte">
          <dte:DTE ID="DatosCertificados">
            <dte:DatosEmision ID="DatosEmision">
              <dte:DatosGenerales Tipo="FACT" FechaHoraEmision="2020-04-22T00:00:00" CodigoMoneda="GTQ" NumeroAcceso="123456789" />
              <dte:Emisor NITEmisor="43430775" NombreEmisor="POLLO CAMPERO S.A." CodigoEstablecimiento="1" NombreComercial="DOCUTEC" CorreoEmisor="info@docutec.com.gt" AfiliacionIVA="GEN">
                <dte:DireccionEmisor>
                  <dte:Direccion>CIUDAD</dte:Direccion>
                  <dte:CodigoPostal>01011</dte:CodigoPostal>
                  <dte:Municipio>GUATEMALA</dte:Municipio>
                  <dte:Departamento>GUATEMALA</dte:Departamento>
                  <dte:Pais>GT</dte:Pais>
                </dte:DireccionEmisor>
              </dte:Emisor>
              <dte:Receptor IDReceptor="CF" NombreReceptor="Consumidor Final." CorreoReceptor="cliente@gmail.com">
                <dte:DireccionReceptor>
                  <dte:Direccion>CIUDAD</dte:Direccion>
                  <dte:CodigoPostal>01010</dte:CodigoPostal>
                  <dte:Municipio>GUATEMALA</dte:Municipio>
                  <dte:Departamento>GUATEMALA</dte:Departamento>
                  <dte:Pais>GT</dte:Pais>
                </dte:DireccionReceptor>
              </dte:Receptor>
              <dte:Frases>
                <dte:Frase TipoFrase="2" CodigoEscenario="1" />
                <dte:Frase TipoFrase="1" CodigoEscenario="2" />
              </dte:Frases>
              <dte:Items>
                <dte:Item NumeroLinea="1" BienOServicio="B">
                  <dte:Cantidad>1.000000</dte:Cantidad>
                  <dte:UnidadMedida>UNI</dte:UnidadMedida>
                  <dte:Descripcion>DESCRIPCION DE 10,000 CARACTERES.</dte:Descripcion>
                  <dte:PrecioUnitario>100.000000</dte:PrecioUnitario>
                  <dte:Precio>100.000000</dte:Precio>
                  <dte:Descuento>0.00</dte:Descuento>
                  <dte:Impuestos>
                    <dte:Impuesto>
                      <dte:NombreCorto>IVA</dte:NombreCorto>
                      <dte:CodigoUnidadGravable>1</dte:CodigoUnidadGravable>
                      <dte:MontoGravable>89.28</dte:MontoGravable>
                      <dte:MontoImpuesto>10.71</dte:MontoImpuesto>
                    </dte:Impuesto>
                  </dte:Impuestos>
                  <dte:Total>100.00</dte:Total>
                </dte:Item>
              </dte:Items>
              <dte:Totales>
                <dte:TotalImpuestos>
                  <dte:TotalImpuesto NombreCorto="IVA" TotalMontoImpuesto="10.71" />
                </dte:TotalImpuestos>
                <dte:GranTotal>100.00</dte:GranTotal>
              </dte:Totales>
            </dte:DatosEmision>
          </dte:DTE>
        </dte:SAT>
      </dte:GTDocumento>]]></tem:DocumentContent>
         <!--Optional:-->
         <tem:Connector>Xslt</tem:Connector>
         <tem:ConvertDocument>true</tem:ConvertDocument>
         <tem:SignDocument>true</tem:SignDocument>
         <tem:PrintDocument>true</tem:PrintDocument>
      </tem:CreateDocumentWithCustomResponse>
   </soapenv:Body>
</soapenv:Envelope> """





url="https://pruebasfel.g4sdocumenta.com/webservicefront/factwsfront.asmx"
#headers = {'content-type': 'application/soap+xml';charset=utf-8}
headers = {'content-type': 'application/soap+xml'}
body = """<?xml version="1.0" encoding="UTF-8"?>
         <SOAP-ENV:Envelope xmlns:ns0="http://ws.cdyne.com/WeatherWS/" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
            <SOAP-ENV:Header/>
              <ns1:Body><ns0:GetWeatherInformation/></ns1:Body>
         </SOAP-ENV:Envelope>"""

response = requests.post(url,data=xml,headers=headers)
print(response.content)




# imp = Import('http://www.w3.org/2001/XMLSchema',
#              location='http://www.w3.org/2001/XMLSchema.xsd')
# imp.filter.add('http://www.fact.com.mx/schema/ws')
#imp = Import('http://www.w3.org/2001/XMLSchema')
#imp.filter.add('http://www.fact.com.mx/schema/ws')
# doctor = ImportDoctor(imp)


#client = Client(url, doctor=ImportDoctor(imp))

client = Client(url)

_edx = client.factory.create('CreateDocumentWithCustomResponse')

_edx.Area = 'FELODOO'
_edx.Password  = 'administrador'
_edx.DocumentType  = 'FACT'
_edx.DocumentContent = xml
_edx.Connector = 'Xslt'
_edx.ConvertDocument = True
_edx.SignDocument = True
_edx.PrintDocument = True

invoice_info = client.service.CreateDocumentWithCustomResponse(_edx)

print('edx')





