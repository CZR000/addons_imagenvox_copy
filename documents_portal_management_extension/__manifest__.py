# -*- coding: utf-8 -*-
{
    'name': 'Documents Portal Management - Extension',
    'version': '18.0.7.7.0',
    'summary': 'Custom extensions for Documents Portal Management module',
    'description': """
        Customizations over documents_portal_management:
    """,
    'author': 'Empiria',
    'category': 'Document Management',
    'depends': [
        'web', 
        'website', 
        'portal',
        'documents_portal_management',
        'documents_portal_auto_folder',
    ],
    'data': [
        'security/ir_rule.xml', 
        'views/ir_attachment_all_views_inherit.xml',
        'views/folders_dialog_view.xml',
        'views/folders_views_inherit.xml',
        'views/menus.xml',
        'views/portal_templates_inherit.xml',
        'data/folder_last_update_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'documents_portal_management_extension/static/src/js/attachment_action_buttons.js',
            'documents_portal_management_extension/static/src/xml/attachment_action_buttons.xml',
            'documents_portal_management_extension/static/src/scss/attachment_action_buttons.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
