# -*- encoding: utf-8 -*-

from odoo import models, fields, api, exceptions

class hr_employee(models.Model):

    _inherit = 'hr.employee'

    nit=fields.Char('NIT',size=30)
    igss=fields.Char('No. Afiliación',size=30)
    nombre1=fields.Char('1er. Nombre',size=50)
    nombre2=fields.Char('2do. Nombre',size=50)
    apellido1=fields.Char('1er. Apellido',size=50)
    apellido2=fields.Char('2do. Apellido',size=50)
    apellido_casada=fields.Char('Apellido casada',size=50)
    irtra=fields.Char('IRTRA',size=50)
    dpi_extendido=fields.Char('DPI extendido en ',size=50)
    codigo_interno=fields.Char('Código interno ',size=50)
    conyuge=fields.Char('Conyuge',size=50)
    puesto_minitrab_id = fields.Many2one('puesto_minitrab',string='Puesto Minitrab')
    identificacion_minitrab_id = fields.Many2one('identificacion_minitrab',string='Tipo Identificación')
    dpi=fields.Char('DPI',size=30)
    lugar_nacimiento_minitrab_id = fields.Many2one('lugar_nacimiento_minitrab',string='Lugar de Nacimiento Minitrab')
    pais_origen_minitrab_id = fields.Many2one('pais_origen_minitrab',string='Pais de origen Minitrab')
    nivel_academico_minitrab_id = fields.Many2one('nivel_academico_minitrab',string='Nivel Academico Minitrab')
    profesion_minitrab_id = fields.Many2one('profesion_minitrab',string='Profesión Minitrab')
    etnia_minitrab_id = fields.Many2one('etnia_minitrab',string='Etnia Minitrab')
    idioma_minitrab_id = fields.Many2one('idioma_minitrab',string='Idioma Minitrab')
    forma_pago_id = fields.Many2one('forma_pago',string='Forma de Pago', required=True)
    cuenta_bancaria=fields.Char('Cuenta bancaria',size=20)
    tipo_contrato=fields.Char('Tipo contrato',size=20)
    inicio_labores=fields.Date('Inicio labores')
    reinicio_labores=fields.Date('Reinicio labores')
    fecha_retiro=fields.Date('Fecha retiro ')
    jornada=fields.Char('Jornada',size=30)
    jornada_minitrab_id = fields.Many2one('jornada_minitrab', string='Jornada Minitrab')
    dias_laborados_ano=fields.Integer('Días laborados en un año ')
    permisos_trabajo=fields.Float('Permisos en el trabajo')
    salario_anual_nominal=fields.Float('Salario anual nominal')
    bonificacion_decreto=fields.Float('Bonificacion 78 89')
    extras_anuales=fields.Float('Total extras anuales')
    valor_extra=fields.Float('Valor de hora extra')
    aguinaldo=fields.Float('Monto aguinaldo')
    bono14=fields.Float('Monto bono 14 42 92')
    redistribucion_por_comision=fields.Float('Redistribución por comisión')
    viaticos=fields.Float('Viaticos')   
    bonificaciones=fields.Float('Bonificaciones adicionales')
    redistribucion_vacaciones=fields.Float('Redistribucion por vacaciones')
    redistribucion_indemnizacion=fields.Float('Redistribucion por indemnizacion')
    ex_empleado = fields.Boolean('Ex-empleado')
    tipo_sangre_id = fields.Many2one('tipo_sangre', string='Tipo de Sangre')
    tipo_discapacidad_minitrab_id = fields.Many2one('tipo_discapacidad_minitrab', string='Tipo de Discapacidad Minitrab')
    trabajo_en_el_extranjero_minitrab = fields.Boolean('Ha trabajado en el extranjero')
    ocupacion_extranjero_minitrab_id = fields.Many2one('puesto_minitrab', string='Ocupación en el extranjero Minitrab')
    motivo_finalizacion_relacion_le=fields.Char('Motivo finalización relación laboraral en el extranjero',size=50)

class hr_contract(models.Model):
    
    _inherit = 'hr.contract'

    #Ingresos    
    primera_quincena=fields.Float('1ra. quincena')
    segunda_quincena=fields.Float('2da. quincena')
    horas_extras=fields.Float('Horas extras diurnas')
    horas_extras2=fields.Float('Horas extras nocturnas')
    otra_bonificacion=fields.Float('Otra bonificación')
    dias_laborados=fields.Float('Dias laborados 1ra quincena')
    dias_laborados2=fields.Float('Dias laborados 2da quincena')
    comisiones=fields.Float('Comisiones')
    ingresos1=fields.Float('Otros ingresos 1')
    ingresos2=fields.Float('Otros ingresos 2')
    ingresos3=fields.Float('Otros ingresos 3')
    ingresos4=fields.Float('Otros ingresos 4')
    ingresos5=fields.Float('Otros ingresos 5')

    #Descuentos
    isr=fields.Float('ISR')
    prestamo=fields.Float('Préstamo')
    telefono=fields.Float('Teléfono')
    otros=fields.Float('Otros 1')
    otros2=fields.Float('Otros 2')
    otros3=fields.Float('Otros 3')
    otros4=fields.Float('Otros 4')
    otros5=fields.Float('Otros 5')
    uniforme = fields.Float('Uniforme')
    herramienta = fields.Float('Herramienta')
    anticipo_salario = fields.Float('Anticipo Salario')
    ayuvi = fields.Float('AYUVI')
    cafeteria = fields.Float('Cafetería')
    viaticos = fields.Float('Viáticos')
    descuento_judicial = fields.Float('Descuento Judicial')
    bantrab=fields.Float('Bantrab')
    ornato=fields.Float('Boleto Ornato')
    danios_vehiculos = fields.Float('Daños a Vehículos')
    facturacion_interna = fields.Float('Facturacón Interna')
    danios_terceros = fields.Float('Daños a Terceros')

    dias_igss=fields.Float('Días de suspensión del Igss')
    dias_falta=fields.Float('Días de suspensión por faltas')

    tipo_contrato_minitrab_id = fields.Many2one('tipo_contrato_minitrab', string='Tipo de Contrato Minitrab')
    temporalidad_contrato_minitrab_id = fields.Many2one('temporalidad_contrato_minitrab', string='Temporalidad del Contrato Minitrab')

    #cheques
    diario_cheques_id = fields.Many2one('account.journal',string='Diario cheque')
    x_reglas_dias_ids = fields.One2many('x_reglas_dias', 'x_contract_id',string='Reglas/Dias')

class hr_salary_rule(models.Model):
    
    _inherit = 'hr.salary.rule'

    # Configuraciones para los recibos.
    titulo_detalle = fields.Boolean('Titulo detalle')
    pie_detalle = fields.Boolean('Pie detalle')
    imprime_recibo = fields.Boolean('Imprime en recibo')
    ingreso_egreso = fields.Selection([('ingreso', 'Ingreso'), ('egreso', 'Egreso'),], 'Ingreso/Egreso', select=True)
    
    # Configuraciones para el reporte de nominas.
    imprime_reporte  = fields.Boolean('Imprime en reporte de planillas ')
    orden_columna    = fields.Float('Orden ')
    titulos_columnas=fields.Char('Titulo de columna',size=30)

    # Reporte del banco.
    imprime_liquido  = fields.Boolean('Liquido a recibir ')
    
    # Configuraciones para el reporte de libro de salarios.
    imprime_reporte_ls  = fields.Boolean('Imprime en Libro de Salarios ')
    orden_columna_ls    = fields.Float('Orden ')
    suma_regla          = fields.Integer('Suma ')
    titulos_columnas_ls=fields.Char('Titulo de columna',size=30)

class reglas_dias(models.Model):
    
    _name = 'x_reglas_dias'

    name          = fields.Char(string="Descripción ", default='regla')
    x_rule_id     = fields.Many2one('hr.salary.rule', 'Regla ')
    x_contract_id = fields.Many2one('hr.contract', 'Contrato ')
    x_dias        = fields.Integer('Cantidad ')