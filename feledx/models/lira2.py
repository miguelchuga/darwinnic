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


xml = """<?xml version="1.0" encoding="UTF-8"?>
<dte:GTDocumento xmlns:dte="http://www.sat.gob.gt/dte/fel/0.2.0" xmlns:cex="http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0" xmlns:cfc="http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0" xmlns:cfe="http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0" xmlns:cno="http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" Version="0.1">
   <dte:SAT ClaseDocumento="dte">
      <dte:DTE ID="DatosCertificados">
         <dte:DatosEmision ID="DatosEmision">
            <dte:DatosGenerales Tipo="RECI" FechaHoraEmision="2020-06-18T09:16:00" CodigoMoneda="GTQ" />
            <dte:Emisor NITEmisor="2391597" NombreEmisor="SOCIEDAD PROTECTORA DEL NIÑO" CodigoEstablecimiento="3" NombreComercial="TIENDA AEROPUERTO DE SOCIEDAD PROTECTORA DEL NIÑO " AfiliacionIVA="EXE">
               <dte:DireccionEmisor>
                  <dte:Direccion>AEROPUERTO INTERNACIONAL LA AURORA Zona 13 TERMINAL AEREA</dte:Direccion>
                  <dte:CodigoPostal>01000</dte:CodigoPostal>
                  <dte:Municipio>GUATEMALA</dte:Municipio>
                  <dte:Departamento>Guatemala</dte:Departamento>
                  <dte:Pais>GT</dte:Pais>
               </dte:DireccionEmisor>
            </dte:Emisor>
            <dte:Receptor IDReceptor="60010207" NombreReceptor="G4S DOCUMENTA SOCIEDAD ANONIMA" />
            <dte:Frases>
               <dte:Frase TipoFrase="4" CodigoEscenario="6" />
            </dte:Frases>
            <dte:Items>
               <dte:Item NumeroLinea="1" BienOServicio="B">
                  <dte:Cantidad>1.00000000</dte:Cantidad>
                  <dte:UnidadMedida>UNO</dte:UnidadMedida>
                  <dte:Descripcion>PRODUCTO DE PRUEBAS</dte:Descripcion>
                  <dte:PrecioUnitario>300.00</dte:PrecioUnitario>
                  <dte:Precio>300.00</dte:Precio>
                  <dte:Descuento>0</dte:Descuento>
                  <dte:Total>300</dte:Total>
               </dte:Item>
            </dte:Items>
            <dte:Totales>
               <dte:GranTotal>300.00</dte:GranTotal>
            </dte:Totales>
         </dte:DatosEmision>
      </dte:DTE>
   </dte:SAT>
</dte:GTDocumento>"""






xml64_bytes = xml.encode('utf-8')
print(xml64_bytes)
xml64e = base64.b64encode(xml64_bytes)
xml64d = base64.b64decode(xml64e)

b='PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPGR0ZTpHVERvY3VtZW50byB4bWxuczpkdGU9Imh0dHA6Ly93d3cuc2F0LmdvYi5ndC9kdGUvZmVsLzAuMi4wIiB4bWxuczpjZXg9Imh0dHA6Ly93d3cuc2F0LmdvYi5ndC9mYWNlMi9Db21wbGVtZW50b0V4cG9ydGFjaW9uZXMvMC4xLjAiIHhtbG5zOmNmYz0iaHR0cDovL3d3dy5zYXQuZ29iLmd0L2R0ZS9mZWwvQ29tcENhbWJpYXJpYS8wLjEuMCIgeG1sbnM6Y2ZlPSJodHRwOi8vd3d3LnNhdC5nb2IuZ3QvZmFjZTIvQ29tcGxlbWVudG9GYWN0dXJhRXNwZWNpYWwvMC4xLjAiIHhtbG5zOmNubz0iaHR0cDovL3d3dy5zYXQuZ29iLmd0L2ZhY2UyL0NvbXBsZW1lbnRvUmVmZXJlbmNpYU5vdGEvMC4xLjAiIHhtbG5zOmRzPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwLzA5L3htbGRzaWcjIiB4bWxuczp4c2k9Imh0dHA6Ly93d3cudzMub3JnLzIwMDEvWE1MU2NoZW1hLWluc3RhbmNlIiBWZXJzaW9uPSIwLjEiPgogICA8ZHRlOlNBVCBDbGFzZURvY3VtZW50bz0iZHRlIj4KICAgICAgPGR0ZTpEVEUgSUQ9IkRhdG9zQ2VydGlmaWNhZG9zIj4KICAgICAgICAgPGR0ZTpEYXRvc0VtaXNpb24gSUQ9IkRhdG9zRW1pc2lvbiI+CiAgICAgICAgICAgIDxkdGU6RGF0b3NHZW5lcmFsZXMgVGlwbz0iUkVDSSIgRmVjaGFIb3JhRW1pc2lvbj0iMjAyMC0wNi0xOFQwOToxNjowMCIgQ29kaWdvTW9uZWRhPSJHVFEiIC8+CiAgICAgICAgICAgIDxkdGU6RW1pc29yIE5JVEVtaXNvcj0iMjM5MTU5NyIgTm9tYnJlRW1pc29yPSJTT0NJRURBRCBQUk9URUNUT1JBIERFTCBOScORTyIgQ29kaWdvRXN0YWJsZWNpbWllbnRvPSIzIiBOb21icmVDb21lcmNpYWw9IlRJRU5EQSBBRVJPUFVFUlRPIERFIFNPQ0lFREFEIFBST1RFQ1RPUkEgREVMIE5Jw5FPICIgQWZpbGlhY2lvbklWQT0iRVhFIj4KICAgICAgICAgICAgICAgPGR0ZTpEaXJlY2Npb25FbWlzb3I+CiAgICAgICAgICAgICAgICAgIDxkdGU6RGlyZWNjaW9uPkFFUk9QVUVSVE8gSU5URVJOQUNJT05BTCBMQSBBVVJPUkEgWm9uYSAxMyBURVJNSU5BTCBBRVJFQTwvZHRlOkRpcmVjY2lvbj4KICAgICAgICAgICAgICAgICAgPGR0ZTpDb2RpZ29Qb3N0YWw+MDEwMDA8L2R0ZTpDb2RpZ29Qb3N0YWw+CiAgICAgICAgICAgICAgICAgIDxkdGU6TXVuaWNpcGlvPkdVQVRFTUFMQTwvZHRlOk11bmljaXBpbz4KICAgICAgICAgICAgICAgICAgPGR0ZTpEZXBhcnRhbWVudG8+R3VhdGVtYWxhPC9kdGU6RGVwYXJ0YW1lbnRvPgogICAgICAgICAgICAgICAgICA8ZHRlOlBhaXM+R1Q8L2R0ZTpQYWlzPgogICAgICAgICAgICAgICA8L2R0ZTpEaXJlY2Npb25FbWlzb3I+CiAgICAgICAgICAgIDwvZHRlOkVtaXNvcj4KICAgICAgICAgICAgPGR0ZTpSZWNlcHRvciBJRFJlY2VwdG9yPSI2MDAxMDIwNyIgTm9tYnJlUmVjZXB0b3I9Ikc0UyBET0NVTUVOVEEgU09DSUVEQUQgQU5PTklNQSIgLz4KICAgICAgICAgICAgPGR0ZTpGcmFzZXM+CiAgICAgICAgICAgICAgIDxkdGU6RnJhc2UgVGlwb0ZyYXNlPSI0IiBDb2RpZ29Fc2NlbmFyaW89IjYiIC8+CiAgICAgICAgICAgIDwvZHRlOkZyYXNlcz4KICAgICAgICAgICAgPGR0ZTpJdGVtcz4KICAgICAgICAgICAgICAgPGR0ZTpJdGVtIE51bWVyb0xpbmVhPSIxIiBCaWVuT1NlcnZpY2lvPSJCIj4KICAgICAgICAgICAgICAgICAgPGR0ZTpDYW50aWRhZD4xLjAwMDAwMDAwPC9kdGU6Q2FudGlkYWQ+CiAgICAgICAgICAgICAgICAgIDxkdGU6VW5pZGFkTWVkaWRhPlVOTzwvZHRlOlVuaWRhZE1lZGlkYT4KICAgICAgICAgICAgICAgICAgPGR0ZTpEZXNjcmlwY2lvbj5QUk9EVUNUTyBERSBQUlVFQkFTPC9kdGU6RGVzY3JpcGNpb24+CiAgICAgICAgICAgICAgICAgIDxkdGU6UHJlY2lvVW5pdGFyaW8+MzAwLjAwPC9kdGU6UHJlY2lvVW5pdGFyaW8+CiAgICAgICAgICAgICAgICAgIDxkdGU6UHJlY2lvPjMwMC4wMDwvZHRlOlByZWNpbz4KICAgICAgICAgICAgICAgICAgPGR0ZTpEZXNjdWVudG8+MDwvZHRlOkRlc2N1ZW50bz4KICAgICAgICAgICAgICAgICAgPGR0ZTpUb3RhbD4zMDA8L2R0ZTpUb3RhbD4KICAgICAgICAgICAgICAgPC9kdGU6SXRlbT4KICAgICAgICAgICAgPC9kdGU6SXRlbXM+CiAgICAgICAgICAgIDxkdGU6VG90YWxlcz4KICAgICAgICAgICAgICAgPGR0ZTpHcmFuVG90YWw+MzAwLjAwPC9kdGU6R3JhblRvdGFsPgogICAgICAgICAgICA8L2R0ZTpUb3RhbGVzPgogICAgICAgICA8L2R0ZTpEYXRvc0VtaXNpb24+CiAgICAgIDwvZHRlOkRURT4KICAgPC9kdGU6U0FUPgo8L2R0ZTpHVERvY3VtZW50bz4='

data = {
    'Requestor': 'E8F8E24B-EF76-4EB6-B93B-5DF69E43FA92',
    'Transaction': 'SYSTEM_REQUEST',
    'Country': 'GT',
    'Entity': '2391597',
    'User': 'E8F8E24B-EF76-4EB6-B93B-5DF69E43FA92',
    'UserName':  'ADMINISTRADOR',
    'Data1': 'POST_DOCUMENT_SAT',
    'Data2': xml64e,
    'Data3':''
}


wsdl = 'https://pruebasfel.g4sdocumenta.com/webservicefront/factwsfront.asmx?WSDL'
client = zeep.Client(wsdl=wsdl)
result = client.service.RequestTransaction(Requestor='E8F8E24B-EF76-4EB6-B93B-5DF69E43FA92', Transaction= 'SYSTEM_REQUEST',Country='GT',Entity= '2391597',User= 'E8F8E24B-EF76-4EB6-B93B-5DF69E43FA92',UserName=  'ADMINISTRADOR',Data1= 'POST_DOCUMENT_SAT',Data2= b)


print(xml64e)
print(xml64d)
print(b)
print('fin')

