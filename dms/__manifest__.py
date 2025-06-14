# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Document Management System",
    "summary": """Document Management System for Odoo""",
    "version": "14.0.4.0.0",
    "category": "Document Management",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/dms",
    "author": "MuK IT, Tecnativa, Odoo Community Association (OCA)",
    "depends": [
        "web_drop_target",
        "mail",
        "http_routing",
        "portal",
        "mail_preview_base",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "actions/file.xml",
        "template/assets.xml",
        "template/onboarding.xml",
        "views/menu.xml",
        "views/tag.xml",
        "views/category.xml",
        "views/dms_file.xml",
        "views/directory.xml",
        "views/storage.xml",
        "views/dms_access_groups_views.xml",
        "views/res_config_settings.xml",
        "views/dms_portal_templates.xml",
    ],
    "qweb": ["static/src/xml/views.xml"],
    "demo": [
        "demo/res_users.xml",
        "demo/access_group.xml",
        "demo/category.xml",
        "demo/tag.xml",
        "demo/storage.xml",
        "demo/directory.xml",
        "demo/file.xml",
        "demo/assets.xml",
    ],
    "images": ["static/description/banner.png"],
    "application": True,
    'assets': {
        'web.assets_backend': [
            '/dms/static/src/js/openfolder.js',
        ]
        },
}
