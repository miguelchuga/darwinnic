# -*- coding: utf-8 -*-
# from odoo import http


# class Jasper(http.Controller):
#     @http.route('/jasper/jasper/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/jasper/jasper/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('jasper.listing', {
#             'root': '/jasper/jasper',
#             'objects': http.request.env['jasper.jasper'].search([]),
#         })

#     @http.route('/jasper/jasper/objects/<model("jasper.jasper"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('jasper.object', {
#             'object': obj
#         })
