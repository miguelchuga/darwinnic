# -*- coding: utf-8 -*-
import urllib.request
import base64

url="https://report.feel.com.gt/ingfacereport/ingfacereport_documento?uuid=822718B3-343E-4AF3-A422-8194D0B1D101"

response =  urllib.request.urlopen(url)

data = response.read()

with open('/home/cmike/mc/prueba.pdf', 'wb') as archivo:archivo.write(data)





print("miguel")