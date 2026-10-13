# -*- coding: utf-8 -*-
{
    'name': 'POS Custom Fields',
    'version': '18.0.1.0.3',
    'category': 'Point of Sale',
    'summary': 'Campos personalizados para Punto de Venta',
    'description': """
        Módulo de personalización para Punto de Venta
        * Cambia etiqueta de Cliente a Paciente en órdenes POS
        * Agrega campo de tags basado en vendedores de las líneas
    """,
    'author': 'Empiria',
    'depends': [
        'point_of_sale',
        'pos_salesperson_employee',
    ],
    'data': [
        'views/pos_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',

}


