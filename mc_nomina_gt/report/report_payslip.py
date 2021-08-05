#-*- coding:utf-8 -*-

from odoo import models, fields, api, _
from odoo.osv import osv
from odoo.report import report_sxw
from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

class hr_payslip_line(models.Model):

    _inherit = 'hr.payslip'

    @api.model
    def get_payslip_titulo(self):
        payslip_titulo_obj = self.env['hr.payslip.line']
        payslip_titulo_ids=payslip_titulo_obj.search([('slip_id', '=', self.id), ('appears_on_payslip', '=', True), ('salary_rule_id.titulo_detalle', '=', True), ('salary_rule_id.imprime_recibo', '=', True)])
        res_ing=payslip_titulo_obj.browse(payslip_titulo_ids)._ids

        return res_ing
     
    @api.model
    def get_payslip_ingresos(self):
        payslip_line_obj = self.env['hr.payslip.line']
        payslip_line_ids=payslip_line_obj.search([('slip_id', '=', self.id), ('salary_rule_id.ingreso_egreso', '=', 'ingreso'), ('appears_on_payslip', '=', True), ('total', '>', '0')])
        res_ing=payslip_line_obj.browse(payslip_line_ids)._ids

        return res_ing 
    
    @api.model
    def get_payslip_egresos(self):
        payslip_line_obj = self.env['hr.payslip.line']
        payslip_line_ids=payslip_line_obj.search([('slip_id', '=', self.id), ('salary_rule_id.ingreso_egreso', '=', 'egreso'), ('appears_on_payslip', '=', True), ('total', '>', '0')])
        res_ing=payslip_line_obj.browse(payslip_line_ids)._ids

        return res_ing 

    @api.model
    def get_payslip_pie(self):
        payslip_pie_obj = self.env['hr.payslip.line']
        payslip_pie_ids=payslip_pie_obj.search([('slip_id', '=', self.id), ('appears_on_payslip', '=', True), ('salary_rule_id.pie_detalle', '=', True), ('salary_rule_id.imprime_recibo', '=', True)])
        res_ing=payslip_pie_obj.browse(payslip_pie_ids)._ids

        return res_ing 

'''
class payslip_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(payslip_report, self).__init__(cr, uid, name, context)

class wrapped_report_payslip(osv.AbstractModel):
    _name = 'report.mc_nomina_gt.report_recibos'
    _inherit = 'report.abstract_report'
    _template = 'mc_nomina_gt.report_recibos'
    _wrapped_report_class = payslip_report

class wrapped_report_payslip2(osv.AbstractModel):
    _name = 'report.mc_nomina_gt.report_recibos_carta'
    _inherit = 'report.abstract_report'
    _template = 'mc_nomina_gt.report_recibos_carta'
    _wrapped_report_class = payslip_report

'''