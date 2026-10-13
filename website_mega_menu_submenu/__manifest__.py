# -*- coding: utf-8 -*-
{
    'name': 'Website Mega Menu - Submenús',
    'version': '18.0.2.0.3',
    'category': 'Website',
    'summary': 'Agrega capacidad de submenús dentro de Mega Menús',
    'description': """
        Permite agregar submenús desplegables dentro del contenido 
        del mega menú sin afectar la funcionalidad estándar.
    """,
    'author': 'Empiria',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [
        'security/ir.model.access.csv',
        'views/website_menu_views.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_mega_menu_submenu/static/src/scss/mega_menu_submenu.scss',
            'website_mega_menu_submenu/static/src/js/mega_menu_submenu.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,

}

