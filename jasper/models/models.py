# -*- coding: utf-8 -*-
import odoo
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import MissingError, UserError, ValidationError, AccessError
from base64 import encodestring as ttt
from requests import Session as xxx
import ast
#from odoo.tools.safe_eval import safe_eval




class CargarLibrerias(models.Model):
    _name = "jasper.server"
    _description = "jasperserver"

    reporte = fields.Char('Nombre de reporte', size=160, store=True)
    consulta = fields.Char('datos query', store=True)
    parametros = fields.Char('parametros', store=True)

    def jasperserver(self, nombre_reporte, query):
        usuario = self.env['ir.config_parameter'].search([('key', '=', 'jasperuser')])[0].value
        pasword = self.env['ir.config_parameter'].search([('key', '=', 'jssperpass')])[0].value
        url = self.env['ir.config_parameter'].search([('key', '=', 'jasperserver')])[0].value
        datos = self.env['jasper.server'].search([('reporte','=',nombre_reporte)])[0].consulta
        varjson = ast.literal_eval(datos)
        varjson.update(query)
        print(query)
        print(varjson)
        s =  xxx()
        w = s.get(url, auth =(usuario,pasword), params=varjson)
        return ttt(w.content)
