# -*- coding: utf-8 -*-

{
    'name': 'Loans',
    'version': '13',
    'summary': 'Manage Loan Requests',
    'description': """
        """,
    'category': 'HR',
    'author': "Mohannad Sayed",
    'website': "https://github.com/mohannad-sayed",
    'depends': [
        'base', 'om_hr_payroll_account', 'hr', 'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/hr_loan_seq.xml',
        'data/salary_rule_loan.xml',
        'views/hr_loan.xml',
        'views/hr_payroll.xml',
    ],
    'demo': [],
}
