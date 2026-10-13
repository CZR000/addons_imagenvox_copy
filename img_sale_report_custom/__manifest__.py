# -*- coding: utf-8 -*-
{
    "name": "IMAGEN VOX: Custom Reporte de Ventas",
    "summary": "Permite mostrar u ocultar el IGV en el cuadro de totales del PDF de Ventas por compañía.",
    "description": """
        Añade configuración Multiempresa para el reporte de Ventas.
        Permite a cada empresa ocultar la fila de Impuestos (IGV) en la caja de totales 
        exclusivamente para Cotizaciones/Pedidos de Venta, sin afectar Facturas ni Compras.
    """,
    "author": "Empiria",
    "category": "Sales",
    "version": "18.0.1.0.1",
    "license": "OPL-1",
    "depends": [
        "sale_management",
        "account",
    ],
    "data": [
        "views/res_config_settings_views.xml",
        "report/ir_actions_report_templates.xml",
    ],
    "installable": True,
    "application": False,
}
