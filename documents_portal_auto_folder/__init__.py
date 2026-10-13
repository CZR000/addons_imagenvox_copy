# -*- coding: utf-8 -*-

from . import controllers
from . import models

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Se ejecuta una sola vez al instalar documents_portal_auto_folder.
    Crea carpetas personales para todos los usuarios de portal
    que existían antes de la instalación del módulo.
    """
    portal_group = env.ref("base.group_portal", raise_if_not_found=False)
    if not portal_group:
        _logger.warning("post_init_hook: no se encontró base.group_portal.")
        return

    users = env["res.users"].sudo().search([
        ("groups_id", "in", [portal_group.id]),
        ("portal_folder_id", "=", False),
        ("active", "=", True),
    ])

    _logger.info(
        "post_init_hook: %s usuario(s) de portal sin carpeta, procesando...",
        len(users),
    )

    created = 0
    for user in users:
        try:
            user._ensure_portal_folder_exists()
            if user.portal_folder_id:
                created += 1
        except Exception as e:
            _logger.error(
                "post_init_hook: error creando carpeta para %s (ID %s): %s",
                user.name, user.id, e,
            )

    _logger.info("post_init_hook: %s carpeta(s) creadas.", created)