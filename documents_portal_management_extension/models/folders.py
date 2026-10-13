# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DocumentFoldersExtension(models.Model):
    _inherit = 'documents.folders'

    is_principal = fields.Boolean(string="Is Principal Folder", default=False)

    is_patient_directory = fields.Boolean(
        string="Es carpeta de paciente",
        default=False,
        help="Marca esta carpeta como perteneciente a un paciente."
    )
    
    @api.constrains('is_principal', 'parent_folder_id')
    def _check_principal_folder(self):
        for record in self:
            if record.is_principal and record.parent_folder_id:
                raise ValidationError(
                    "Una carpeta principal no puede tener una Carpeta Padre asignada."
                )

    @api.onchange('is_principal')
    def _onchange_is_principal(self):
        if self.is_principal:
            self.parent_folder_id = False

    def action_open_folder_form(self):
        """
        Navega a la vista form completa de la carpeta seleccionada,
        reemplazando la vista actual (sin popup/diálogo).
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'documents.folders',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'current',
        }

    def action_new_attachment(self):
        """
        PUNTO 3: Abre el formulario de creacion de un nuevo archivo (ir.attachment)
        con el campo 'folder_id' pre-cargado con la carpeta actual.

        PUNTO 4: Si la carpeta pertenece a un usuario portal
        (res.users.portal_folder_id apunta a esta carpeta),
        pre-llena shared_user_ids con ese usuario.
        Si la carpeta no esta vinculada a ningun usuario portal,
        shared_user_ids queda vacio (comportamiento por defecto).
        """
        self.ensure_one()

        form_view_id = self.env.ref(
            'documents_portal_management.view_attachment_form_all_documents'
        ).id

        # PUNTO 4: Buscar si existe un usuario portal cuya carpeta asignada
        # es exactamente esta carpeta.
        portal_user = self.env['res.users'].sudo().search(
            [('portal_folder_id', '=', self.id)],
            limit=1,
        )

        default_shared_users = [(6, 0, [portal_user.id])] if portal_user else []

        return {
            'name': _('Nuevo Archivo'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'target': 'current',
            'context': {
                'default_folder_id': self.id,
                'default_shared_user_ids': default_shared_users,
            },
        }
