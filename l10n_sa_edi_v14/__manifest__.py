# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Saudi Arabia - E-invoicing',
    'icon': '/l10n_sa/static/description/icon.png',
    'version': '14.0.0.6',
    'depends': [
        'account_debit_note',
        'l10n_sa_invoice',
        'base_vat',
        'sale'
    ],
    'author': 'Odoo',
    'summary': """
        E-Invoicing, Universal Business Language
    """,
    'description': """
        E-invoice implementation for the Kingdom of Saudi Arabia
    """,
    'category': 'Accounting/Localizations/EDI',
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'data/account_edi_format.xml',
        'data/ubl_21_zatca.xml',
        'data/res_country_data.xml',
        'wizard/l10n_sa_edi_otp_wizard.xml',
        'views/account_tax_views.xml',
        'views/account_journal_views.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/res_config_settings_view.xml',
        'views/report_invoice.xml',
        'views/account_move.xml',
    ],
    'demo': [
        'demo/demo_company.xml',
    ],

}
