# -*- coding: utf-8 -*-
# from odoo import http


# class GithubProjectIntegration(http.Controller):
#     @http.route('/github_project_integration/github_project_integration', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/github_project_integration/github_project_integration/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('github_project_integration.listing', {
#             'root': '/github_project_integration/github_project_integration',
#             'objects': http.request.env['github_project_integration.github_project_integration'].search([]),
#         })

#     @http.route('/github_project_integration/github_project_integration/objects/<model("github_project_integration.github_project_integration"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('github_project_integration.object', {
#             'object': obj
#         })
