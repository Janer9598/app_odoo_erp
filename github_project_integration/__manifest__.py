{
    'name': "GitHub Project Integration JH",

    'summary': """
        Integración de GitHub con Proyectos de Odoo""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Janer Herrera",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Project',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'project'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/github_integration.xml',
        'views/github_branch.xml',
        'views/inherit_project_task.xml',
        'data/cron_tasks.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
}
# -*- coding: utf-8 -*-
