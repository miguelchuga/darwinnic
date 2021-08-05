# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _

class puesto_minitrab(models.Model):
    _name = 'puesto_minitrab'
    _description = 'Puestos Ministerio de Trabajo'

    name=fields.Char('Puesto',required=True)
    code = fields.Char("Código", size=15, required=True)

class identificacion_minitrab(models.Model):
    _name = 'identificacion_minitrab'
    _description = 'Identificacion Ministerio de Trabajo'

    name = fields.Char("Indentificación", size=50, required=True)
    code = fields.Char("Código", size=15, required=True)

class lugar_nacimiento_minitrab(models.Model):
    _name = 'lugar_nacimiento_minitrab'
    _description = 'Lugares de Nacimiento Ministerio de Trabajo'

    name = fields.Char("Lugar de Nacimiento", size=50, required=True)
    code = fields.Char("Código", size=15, required=True)
    
class pais_origen_minitrab(models.Model):
    _name = 'pais_origen_minitrab'
    _description = 'Pais de Origen'
 
    name = fields.Char("País de origen", size=50, required=True)
    code = fields.Char("Código", size=15, required=True)
       
class nivel_academico_minitrab(models.Model):
    _name = 'nivel_academico_minitrab'
    _description = 'Nivel Academico'

    name = fields.Char("Nivel academico", size=50, required=True)
    code = fields.Char("Código", size=15, required=True)

class profesion_minitrab(models.Model):
    _name = 'profesion_minitrab'
    _description = 'Profesion'
  
    name = fields.Char("Profesión", size=50, required=True)
    code = fields.Char("Código", size=15, required=True)
       
class etnia_minitrab(models.Model):
    _name = 'etnia_minitrab'
    _description = 'Etnia'

    name = fields.Char("Etnia", size=50, required=True)
    code = fields.Char("Código", size=15, required=True)

class idioma_minitrab(models.Model):
    _name = 'idioma_minitrab'
    _description = 'Idioma Minitrab'
 
    name = fields.Char("Idioma", size=50, required=True)
    code = fields.Char("Código", size=15, required=True)     
       
class forma_pago(models.Model):
    _name = 'forma_pago'
    _description = 'Forma de Pago'
 
    name = fields.Char("Forma de Pago", size=50, required=True)
    code = fields.Char("Código", size=15, required=True)

class tipo_sangre(models.Model):
    _name = 'tipo_sangre'
    _description = 'Tipo de Sangre'

    name = fields.Char("Tipo de Sangre", size=50, required=True)
    code = fields.Char("Código", size=15, required=True)

class jornada_minitrab(models.Model):
    _name = 'jornada_minitrab'
    _description = 'Jornada Minitrab'

    name = fields.Char("Jornada", size=50, required=True)
    code = fields.Char("Código", size=15, required=True)

class tipo_contrato_minitrab(models.Model):
    _name = 'tipo_contrato_minitrab'
    _description = 'Tipo de Contrato'

    name = fields.Char("Tipo de Contrato", size=50, required=True)
    code = fields.Char("Código", size=15, required=True)

class tipo_discapacidad_minitrab(models.Model):
    _name = 'tipo_discapacidad_minitrab'
    _description = 'Tipo de Discapacidad'

    name = fields.Char("Tipo de Discapacidad", size=50, required=True)
    code = fields.Char("Código", size=15, required=True)

class temporalidad_contrato_minitrab(models.Model):
    _name = 'temporalidad_contrato_minitrab'
    _description = 'Temporalidad del Contrato'

    name = fields.Char("Temporalidad del Contrato", size=50, required=True)
    code = fields.Char("Código", size=15, required=True)