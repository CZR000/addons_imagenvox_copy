# -*- coding: utf-8 -*-
{
    'name': 'Documents Portal - Compartir archivos entre carpetas',
    'version': '18.0.3.3.0',
    'category': 'Document Management',
    'summary': 'Compartir archivos entre carpetas sin duplicar el original',
    'description': """
Compartir archivos entre carpetas sin duplicar
==============================================
Agrega la capacidad de que un mismo ir.attachment aparezca en varias
carpetas (documents.folders) sin duplicar el binario ni el registro.

Características:
----------------
* Campo shared_folder_ids (M2M) en ir.attachment: carpetas invitadas donde
  también se muestra el archivo.
* Campo shared_attachment_ids (M2M inverso) y all_attachment_ids (compute)
  en documents.folders para listar todos los archivos visibles.
* Wizard "Compartir a otras carpetas" con selección múltiple desde el
  header de la lista de Documentos.
* Botón "Quitar de esta carpeta" en filas invitadas: solo remueve del M2M,
  el archivo sigue en la carpeta dueña.
* Botón "Eliminar" en filas dueña: si el archivo está compartido, se
  muestra wizard de confirmación con la cantidad de carpetas afectadas.
* Propagación automática de visibilidad al portal usando shared_user_ids:
  al compartir a una carpeta que pertenece a un usuario portal
  (res.users.portal_folder_id), ese usuario se agrega automáticamente.
    """,
    'author': 'Sinetics',
    'depends': [
        'documents_portal_management',
        'documents_portal_management_extension',
        'documents_portal_bulk_upload',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/share_to_folders_wizard_views.xml',
        'wizards/confirm_delete_attachment_wizard_views.xml',
        'views/documents_folder_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
