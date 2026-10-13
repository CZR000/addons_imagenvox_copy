# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    """
    Herencia de res.users para gestión automática de carpetas documentales.
    Se garantiza que cada usuario de portal tenga su propio directorio.
    """

    _inherit = "res.users"

    portal_folder_id = fields.Many2one(
        comodel_name="documents.folders",
        string="Carpeta del Portal",
        help="Carpeta raíz asignada automáticamente a este usuario de portal.",
        readonly=True,
        ondelete="set null",
        copy=False,  # Al duplicar usuario, no queremos duplicar la referencia a la carpeta
    )

    # ---------------------------------------------------------------------------- #
    #                              TODO - METODOS ORM                              #
    # ---------------------------------------------------------------------------- #
    @api.model_create_multi
    def create(self, vals_list):
        """
        Sobrescribimos create para asignar carpeta post-creación.
        """
        users = super().create(vals_list)
        for user in users:
            # Solo actuamos si es usuario 'share' (Portal/Público) y no tiene carpeta
            if user.share and not user.portal_folder_id:
                user._ensure_portal_folder_exists()
        return users

    def write(self, vals):
        """
        Detectamos cambios de estado (interno -> portal) y cambios de nombre
        para mantener la carpeta sincronizada.
        """
        res = super().write(vals)

        for user in self:
            # Caso 1: Se convirtió en usuario de portal o se reactivó
            if user.share and not user.portal_folder_id:
                user._ensure_portal_folder_exists()

            # Caso 2: Si el usuario cambia de nombre, actualizamos la carpeta
            if "name" in vals and user.portal_folder_id:
                # Usamos sudo() porque el usuario podría no tener permisos de escritura en carpetas
                user.portal_folder_id.sudo().write({"name": user.name})

        return res

    # ---------------------------------------------------------------------------- #
    #                                TODO - METODOS                                #
    # ---------------------------------------------------------------------------- #
    def _ensure_portal_folder_exists(self):
        """
        Crea una carpeta en 'documents.folders' vinculada a este usuario.
        Si ya existe o falla la configuración, gestiona el error suavemente.
        """
        self.ensure_one()

        # 1. Validación preventiva
        if self.portal_folder_id:
            return

        # 2. Obtención segura del directorio padre
        # Usamos try/except para no romper el flujo si el módulo de documentos cambió
        try:
            parent_folder = self.env.ref(
                "documents_portal_management.portal_folder", raise_if_not_found=True
            )
        except ValueError:
            _logger.error(
                _(
                    "Error Crítico: No se encontró el XML ID 'documents_portal_management.portal_folder'. "
                    "No se puede crear la carpeta para el usuario %s"
                ),
                self.name,
            )
            # No lanzamos raise UserError para no bloquear la creación del usuario.
            return

        # 3. Definición del nombre
        # Usamos self.name directo. Si está vacío, usamos login o un fallback.
        folder_name = (
            self.name or self.partner_id.name or self.login or "Usuario Sin Nombre"
        )

        # 4. Preparación de valores
        folder_vals = {
            "name": folder_name,
            "parent_folder_id": parent_folder.id,
            "company_id": self.company_id.id or self.env.company.id,
            # Lógica de negocio: ¿Es directorio portal o personal?
            "is_portal_directory": False,
            "is_personal_directory": True,
        }

        # 5. Creación con privilegios elevados (sudo)
        try:
            new_folder = self.env["documents.folders"].sudo().create(folder_vals)

            # Guardamos la referencia usando sudo para saltar reglas de registro propias
            self.sudo().write({"portal_folder_id": new_folder.id})

            _logger.info(
                f"Carpeta creada exitosamente para: {self.name} (ID Carpeta: {new_folder.id})"
            )

        except Exception as e:
            # Capturamos cualquier otro error de integridad para que no rompa la creación del usuario
            _logger.error(f"Falló la creación de carpeta para {self.name}: {str(e)}")
