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


from zeep import Client

import zeep




xml = """ <?xml version="1.0" encoding="UTF-8"?>
<dte:GTDocumento Version="0.4" xmlns:dte="http://www.sat.gob.gt/dte/fel/0.1.0" xmlns:xd="http://www.w3.org/2000/09/xmldsig#">
    <dte:SAT ClaseDocumento="dte">
        <dte:DTE ID="DatosCertificados">
            <dte:DatosEmision ID="DatosEmision">
                <dte:DatosGenerales CodigoMoneda="GTQ" FechaHoraEmision="2020-05-01T07:50:43-06:00" Tipo="FACT" />
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


xml="""
<?xml version="1.0" encoding="UTF-8"?>
<dte:GTDocumento xmlns:dte="http://www.sat.gob.gt/dte/fel/0.1.0" xmlns:xd="http://www.w3.org/2000/09/xmldsig#" Version="0.4">
   <dte:SAT ClaseDocumento="dte">
      <dte:DTE ID="DatosCertificados">
         <dte:DatosEmision ID="DatosEmision">
            <dte:DatosGenerales CodigoMoneda="GTQ" FechaHoraEmision="2020-05-01T12:06:43-06:00" Tipo="FACT" />
            <dte:Emisor AfiliacionIVA="GEN" CodigoEstablecimiento="False" CorreoEmisor="info@yourcompany.example.com" NITEmisor="C/F" NombreComercial="" NombreEmisor="YourCompany">
               <dte:DireccionEmisor>
                  <dte:Direccion />
                  <dte:CodigoPostal>94134</dte:CodigoPostal>
                  <dte:Municipio>San Francisco</dte:Municipio>
                  <dte:Departamento>California</dte:Departamento>
                  <dte:Pais>GT</dte:Pais>
               </dte:DireccionEmisor>
            </dte:Emisor>
            <dte:Receptor CorreoReceptor="brandon.freeman55@example.com" IDReceptor="CF" NombreReceptor="Brandon Freeman">
               <dte:DireccionReceptor>
                  <dte:Direccion>4557 De Silva St</dte:Direccion>
                  <dte:CodigoPostal>94538</dte:CodigoPostal>
                  <dte:Municipio>Fremont</dte:Municipio>
                  <dte:Departamento>California</dte:Departamento>
                  <dte:Pais>US</dte:Pais>
               </dte:DireccionReceptor>
            </dte:Receptor>
            <dte:Frases>
               <dte:Frase CodigoEscenario="1" TipoFrase="1" />
               <dte:Frase CodigoEscenario="1" TipoFrase="2" />
            </dte:Frases>
            <dte:Items>
               <dte:Item BienOServicio="B" NumeroLinea="1">
                  <dte:Cantidad>1.0</dte:Cantidad>
                  <dte:UnidadMedida>Uni</dte:UnidadMedida>
                  <dte:Descripcion>[E-COM07] Large Cabinet</dte:Descripcion>
                  <dte:PrecioUnitario>320.0</dte:PrecioUnitario>
                  <dte:Precio>320.00</dte:Precio>
                  <dte:Descuento>0.00</dte:Descuento>
                  <dte:Impuestos>
                     <dte:Impuesto>
                        <dte:NombreCorto>IVA</dte:NombreCorto>
                        <dte:CodigoUnidadGravable>1</dte:CodigoUnidadGravable>
                        <dte:MontoGravable>285.71</dte:MontoGravable>
                        <dte:MontoImpuesto>34.29</dte:MontoImpuesto>
                     </dte:Impuesto>
                  </dte:Impuestos>
                  <dte:Total>320.00</dte:Total>
               </dte:Item>
               <dte:Item BienOServicio="B" NumeroLinea="2">
                  <dte:Cantidad>1.0</dte:Cantidad>
                  <dte:UnidadMedida>Uni</dte:UnidadMedida>
                  <dte:Descripcion>[DESK0004] Customizable Desk (CONFIG) (Aluminium, Negro)
160x80cm, con patas grandes.</dte:Descripcion>
                  <dte:PrecioUnitario>800.4</dte:PrecioUnitario>
                  <dte:Precio>800.40</dte:Precio>
                  <dte:Descuento>0.00</dte:Descuento>
                  <dte:Impuestos>
                     <dte:Impuesto>
                        <dte:NombreCorto>IVA</dte:NombreCorto>
                        <dte:CodigoUnidadGravable>1</dte:CodigoUnidadGravable>
                        <dte:MontoGravable>714.64</dte:MontoGravable>
                        <dte:MontoImpuesto>85.76</dte:MontoImpuesto>
                     </dte:Impuesto>
                  </dte:Impuestos>
                  <dte:Total>800.40</dte:Total>
               </dte:Item>
            </dte:Items>
            <dte:Totales>
               <dte:TotalImpuestos>
                  <dte:TotalImpuesto NombreCorto="IVA" TotalMontoImpuesto="120.05" />
               </dte:TotalImpuestos>
               <dte:GranTotal>1120.40</dte:GranTotal>
            </dte:Totales>
         </dte:DatosEmision>
      </dte:DTE>
   </dte:SAT>
</dte:GTDocumento>
"""



wsdl = 'http://edxfeltest.southcentralus.cloudapp.azure.com/CertificacionPDF/Core.asmx?WSDL'
client = zeep.Client(wsdl=wsdl)

result = client.service.CreateDocumentWithCustomResponse(Area='FELODOO', Password='administrador',DocumentType='FACT', DocumentContent=xml, Connector = 'Xslt',ConvertDocument =  True, SignDocument= True, PrintDocument= True, )

#si hay error
pos = result.find('<HasError>')
end = result.find('</HasError>', pos)
error = html.unescape(result[pos+10:end])

if error=='true':
    dte_error = xmltodict.parse(html.unescape(result) .replace('<?xml version="1.0"?>', ''))
else:
    pos = result.find('<![CDATA[')
    if pos >= 0:
        end = result.find(']]', pos)
        doc = html.unescape(result[pos+9:end]).replace('<?xml version="1.0"?>', '')
        dte = xmltodict.parse(doc)
        serie = dte['DTECertification']['DTECertified']['DTE']['dte:GTDocumento']['dte:SAT']['dte:DTE']['dte:Certificacion']['dte:NumeroAutorizacion']['@Serie']
        numero = dte['DTECertification']['DTECertified']['DTE']['dte:GTDocumento']['dte:SAT']['dte:DTE']['dte:Certificacion']['dte:NumeroAutorizacion']['@Numero']
        uuid = dte['DTECertification']['DTECertified']['AuthorizationNumber']
        hora = dte['DTECertification']['DTECertified']['DTE']['dte:GTDocumento']['dte:SAT']['dte:DTE']['dte:Certificacion']['dte:FechaHoraCertificacion']
        #PDF
        pos = result.find('<Buffer>')
        end = result.find('</Buffer>', pos)
        pdf = html.unescape(result[pos+8:end])
print(result)



