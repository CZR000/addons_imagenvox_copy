# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import SQL


class DocumentFoldersExtension(models.Model):
    _inherit = 'documents.folders'

    is_principal = fields.Boolean(string="Is Principal Folder", default=False)

    is_patient_directory = fields.Boolean(
        string="Es carpeta de paciente",
        default=False,
        help="Marca esta carpeta como perteneciente a un paciente."
    )

    last_update_date = fields.Datetime(
        string="Última actualización",
        readonly=True,
        index=True,
        copy=False,
        help="Fecha del último documento subido (o compartido) a esta carpeta "
             "o a alguna de sus subcarpetas.",
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

    # -------------------------------------------------------------------------
    # Última actualización (solo por documentos subidos)
    # -------------------------------------------------------------------------

    def _touch_last_update(self, date=None):
        """Marca la fecha de actualización en estas carpetas y en todos sus padres."""
        if not self:
            return
        date = date or fields.Datetime.now()
        all_folders = self.env['documents.folders']
        folders = self
        while folders:
            all_folders |= folders
            folders = folders.mapped('parent_folder_id') - all_folders
        all_folders.sudo().write({'last_update_date': date})

    def _order_field_to_sql(self, alias, field_name, direction, nulls, query):
        # Al ordenar por "Última actualización", las carpetas sin documentos
        # (fecha vacía) van siempre al final, también en orden descendente.
        if field_name == 'last_update_date' and not nulls.code:
            nulls = SQL("NULLS LAST")
        return super()._order_field_to_sql(alias, field_name, direction, nulls, query)

    @api.model
    def _apply_last_update_dates(self, dates):
        """
        Aplica {folder_id: datetime} a cada carpeta y a sus padres,
        conservando siempre la fecha más reciente.
        """
        Folder = self.sudo()
        for folder_id, date in sorted(dates.items(), key=lambda item: item[1]):
            folder = Folder.browse(folder_id)
            visited = set()
            while folder and folder.id not in visited:
                visited.add(folder.id)
                if not folder.last_update_date or folder.last_update_date < date:
                    folder.last_update_date = date
                folder = folder.parent_folder_id

    @api.model
    def _init_last_update_date(self):
        """
        Rellena el campo en carpetas existentes con la fecha del último
        documento subido. Solo se ejecuta si hay carpetas sin fecha.
        """
        if not self.sudo().search_count([('last_update_date', '=', False)]):
            return
        groups = self.env['ir.attachment'].sudo()._read_group(
            [('folder_id', '!=', False)],
            groupby=['folder_id'],
            aggregates=['create_date:max'],
        )
        self._apply_last_update_dates({
            folder.id: max_date for folder, max_date in groups if max_date
        })

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
