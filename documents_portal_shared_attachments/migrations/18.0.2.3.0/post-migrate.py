# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Recalcula name_normalized con la nueva normalización (sin ningún separador)."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    folders = env['documents.folders'].with_context(active_test=False).search([])
    env.add_to_compute(folders._fields['name_normalized'], folders)
    env.flush_all()