# -*- coding: utf-8 -*-
import base64
import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.documents_portal_management.controllers.portal import (
    CustomerPortal as OriginalPortal,
)

_logger = logging.getLogger(__name__)


class CustomerPortalInherit(OriginalPortal):

    def _get_portal_document_domain(self, user):
        """
        Helper para centralizar el dominio de búsqueda.
        Regla: Ver documentos que están en MI carpeta asignada O documentos compartidos explícitamente.
        """
        domain = [("res_model", "not in", ["ir.ui.view", "ir.module.module"])]

        # 1. Documentos dentro de mi carpeta personal (portal_folder_id)
        # 2. O Documentos donde soy el creador (create_uid)
        # 3. O Documentos compartidos conmigo (shared_user_ids)
        
        user_folder_id = user.portal_folder_id.id or False

        domain += [
            "|",
            "|",
            ("folder_id", "=", user_folder_id),
            ("create_uid", "=", user.id),
            ("shared_user_ids", "in", [user.id]),
        ]
        return domain

    # -------------------------------------------------------------------------
    # SOBRESCRIBIMOS LA VISTA LISTA (Para filtrar lo que ve)
    # -------------------------------------------------------------------------
    def _prepare_home_portal_values(self, counters):
        """
        Actualizamos el contador del Home para que coincida con la nueva lógica
        """
        values = super()._prepare_home_portal_values(counters)
        if "documents_count" in counters:
            user = request.env.user
            Attachment = request.env["ir.attachment"].sudo()

            # Usamos nuestro dominio centralizado
            domain = self._get_portal_document_domain(user)

            values["documents_count"] = (
                Attachment.search_count(domain)
                if Attachment.check_access_rights("read", raise_exception=False)
                else 0
            )
        return values

    # @http.route(
    #     ["/my/documents", "/my/documents/page/<int:page>"],
    #     type="http",
    #     auth="user",
    #     website=True,
    # )
    # def portal_my_documents(
    #     self,
    #     page=1,
    #     date_begin=None,
    #     date_end=None,
    #     sortby=None,
    #     filterby=None,
    #     search=None,
    #     search_in="all",
    #     groupby="none",
    #     **kw,
    # ):
    #     # Ejecutamos el método original para obtener 'values' base
    #     response = super().portal_my_documents(
    #         page,
    #         date_begin,
    #         date_end,
    #         sortby,
    #         filterby,
    #         search,
    #         search_in,
    #         groupby,
    #         **kw,
    #     )

    #     # NOTA TÉCNICA:
    #     # El método original ya hace la búsqueda (search) y paginación.
    #     # Como queremos cambiar fundamentalmente QUÉ documentos se muestran,
    #     # lo más limpio en herencia de controladores complejos es re-inyectar el dominio
    #     # o, lamentablemente, re-ejecutar la lógica si el original no es modular.

    #     # Dado que el original es monolítico, interceptamos la llamada REEMPLAZANDO el dominio antes de buscar.
    #     # Sin embargo, como 'super' ya ejecutó la query, tenemos que hacer un "Monkey Patch" a los valores
    #     # devueltos o reescribir el método completo.

    #     # Para evitar reescribir TODO el método gigante (mala práctica de mantenimiento),
    #     # vamos a filtrar los documentos resultantes o confiar en que el usuario use nuestro método de subida.

    #     # OPCIÓN SENIOR: Reescribir SOLO la parte de la query es difícil sin copiar todo el código.
    #     # Asumiremos reescritura parcial por seguridad y robustez.

    #     # --- INICIO REESCRITURA CON MEJORA ---
    #     values = self._prepare_portal_layout_values()
    #     user = request.env.user
    #     Attachment = request.env["ir.attachment"].sudo()

    #     # AQUÍ ESTÁ EL CAMBIO CLAVE: Usamos el dominio que incluye la carpeta personal
    #     domain = self._get_portal_document_domain(user)

    #     # ... (Resto de filtros de fecha y búsqueda igual que el original) ...
    #     if date_begin and date_end:
    #         domain += [
    #             ("create_date", ">", date_begin),
    #             ("create_date", "<=", date_end),
    #         ]

    #     # ... (Lógica de search y sortby se mantiene igual, la omito por brevedad pero debe ir aquí) ...
    #     # (Debes copiar la lógica de searchbar_sortings, searchbar_inputs, search_in del original aquí)

    #     # Count simplificado para el ejemplo
    #     documents_count = Attachment.search_count(domain)
    #     pager = request.website.pager(
    #         url="/my/documents",
    #         total=documents_count,
    #         page=page,
    #         step=self._items_per_page,
    #         url_args={"date_begin": date_begin, "date_end": date_end, "sortby": sortby},
    #     )

    #     documents = Attachment.search(
    #         domain, limit=self._items_per_page, offset=pager["offset"]
    #     )

    #     values.update(
    #         {
    #             "documents": documents,
    #             "page_name": "documents",
    #             "pager": pager,
    #             "default_url": "/my/documents",
    #             "searchbar_sortings": {},  # Rellenar con las originales
    #             "searchbar_inputs": {},  # Rellenar con las originales
    #         }
    #     )
    #     return request.render("documents_portal_management.portal_my_documents", values)

    # -------------------------------------------------------------------------
    # SOBRESCRIBIMOS LA SUBIDA (Para guardar en SU carpeta)
    # -------------------------------------------------------------------------
    @http.route(
        ["/my/documents/upload_portal_documents/upload"],
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def portal_documents_upload(self, **post):
        """
        Interceptamos la subida para redirigir el archivo a la carpeta personal del usuario (`portal_folder_id`).
        """
        user = request.env.user

        # 1. Aseguramos que el usuario es interno o tiene contexto
        user_sudo = request.env["res.users"].sudo().browse(user.id)

        # 2. Lógica Inteligente de Carpeta
        target_folder_id = user_sudo.portal_folder_id.id

        # Si el usuario no tiene carpeta asignada, intentamos crearla al vuelo
        # usando el método que creamos en el modelo anterior.
        if not target_folder_id and user_sudo.share:
            try:
                user_sudo._ensure_portal_folder_exists()
                target_folder_id = user_sudo.portal_folder_id.id
            except Exception as e:
                _logger.error(
                    f"No se pudo crear carpeta al vuelo para {user.name}: {e}"
                )

        # Fallback: Si todo falla, usar la carpeta general (pero esto no debería pasar con el fix anterior)
        if not target_folder_id:
            portal_directory = request.env.ref(
                "documents_portal_management.portal_folder", raise_if_not_found=False
            )
            target_folder_id = portal_directory.id if portal_directory else False

        try:
            file = post.get("upload_documents", "")
            if not file:
                raise ValidationError(_("No se recibió ningún archivo."))

            stream = file.stream
            fread = stream.read()

            attach_vals = {
                "name": file.filename,
                "folder_id": target_folder_id,  # <--- AQUÍ USAMOS LA CARPETA DEL USUARIO
                "res_name": file.filename,
                "res_model": "res.users",  # Vinculamos al usuario, no al partner, para mayor claridad
                "res_id": user.id,
                "partner_id": user.partner_id.id,
                "datas": base64.encodebytes(fread),
                "is_personal_directory": True,  # Flag útil para filtros
            }

            # Usamos sudo() porque usuarios portal no suelen tener permisos de create en ir.attachment directo
            request.env["ir.attachment"].sudo().create(attach_vals)

        except ValidationError as e:
            return json.dumps({"error_fields": e.args[0]})
        except Exception as e:
            _logger.exception("Error subiendo documento portal")
            return json.dumps(
                {
                    "Error": _("El archivo es inválido o muy grande. Detalle: %s")
                    % (str(e),)
                }
            )

        return request.redirect("/my/documents")
