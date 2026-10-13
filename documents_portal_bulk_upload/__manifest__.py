# -*- coding: utf-8 -*-
{
    'name': 'Documents Portal - Subida Masiva',
    'version': '18.0.1.0.1',
    'summary': 'Subir varios documentos a una carpeta a la vez mediante un asistente.',
    'description': """
Subida Masiva de Documentos
===========================

Agrega un botón "Subir documentos" en la vista de carpeta que despliega un
asistente para cargar varios archivos a la vez. Cada archivo se crea como un
ir.attachment limpio vinculado únicamente a la carpeta (folder_id).

Características:
---------------
* Botón "Subir documentos" en la cabecera de la carpeta.
* Asistente con carga múltiple de archivos (widget many2many_binary).
* Crea un attachment limpio por archivo (solo name, folder_id y datas).
* Independiente del módulo de compartición: si la carpeta tiene comparticiones
  activas, la propagación a usuarios se dispara automáticamente vía el override
  de ir.attachment.create de ese módulo.
""",
    'author': 'Empiria',
    'website': 'https://www.empiria.pe',
    'category': 'Document Management',
    'license': 'LGPL-3',
    'depends': [
        'documents_portal_management_extension',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/documents_folder_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
