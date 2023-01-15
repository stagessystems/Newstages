# -*- coding: utf-8 -*-
{
    'name': "Vacation Settlement",

    'summary': """
        This Module For Settlement of Vacation Leave""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Bander Mansour",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_holidays', 
                'hr', 'mail','sh_message', 'om_hr_payroll'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/effective_date_squence.xml',
        'views/views.xml',
        # 'views/templates.xml',
        'views/effective_date_view.xml',
        'views/hr_employee_view.xml',
        'reports/settlement_form_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
