# -*- coding: utf-8 -*-
from odoo.addons.portal.controllers import portal
from odoo.http import request
from odoo import http, _
from odoo.addons.portal.controllers.portal import pager as portal_pager

class CustomerPortalExtension(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'documents_count' in counters:
            current = values.get('documents_count', 0)
            try:
                current = int(current)
            except (ValueError, TypeError):
                current = 0
            if not current:
                values['documents_count'] = -1
        return values

    # ── VISTA PRINCIPAL: muestra carpetas (folders) ───────────────────────────
    @http.route(
        ['/my/documents', '/my/documents/page/<int:page>'],
        type='http', auth='user', website=True
    )
    def portal_my_documents(self, page=1, **kw):
        user = request.env.user
        user_sudo = request.env['res.users'].sudo().browse(user.id)
    
        Folder = request.env['documents.folders'].sudo()
        Attachment = request.env['ir.attachment'].sudo()
    
        own_folder_id = user_sudo.portal_folder_id.id if (
            hasattr(user_sudo, 'portal_folder_id') and user_sudo.portal_folder_id
        ) else False
    
        attachment_domain = [
            ('res_model', 'not in', ['ir.ui.view', 'ir.module.module']),
            '|',
            ('create_uid', '=', user.id),
            ('shared_user_ids', 'in', [user.id]),
        ]
        user_attachments = Attachment.search(attachment_domain)
    
        folder_ids = set()
        for att in user_attachments:
            if att.shared_folder_ids:
                if own_folder_id and own_folder_id in att.shared_folder_ids.ids:
                    for f in att.shared_folder_ids:
                        if f.is_patient_directory:
                            folder_ids.add(f.id)
            elif att.folder_id:
                folder_ids.add(att.folder_id.id)
    
        folder_ids = list(folder_ids)
    
        if own_folder_id and own_folder_id not in folder_ids:
            folder_ids.append(own_folder_id)
    
        folders = Folder.search([('id', 'in', folder_ids)], order='name asc')
    
        folder_data = []
        for folder in folders:
            count = Attachment.search_count([
                '|',
                ('folder_id', '=', folder.id),
                ('shared_folder_ids', 'in', folder.id),
                ('res_model', 'not in', ['ir.ui.view', 'ir.module.module']),
                '|',
                ('create_uid', '=', user.id),
                ('shared_user_ids', 'in', [user.id]),
            ])
            folder_data.append({
                'folder': folder,
                'count': count,
            })
    
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'documents',
            'folder_data': folder_data,
            'has_folders': bool(folder_data),
        })
        return request.render(
            'documents_portal_management_extension.portal_my_documents_folders',
            values,
        )

    # ── VISTA DE ARCHIVOS POR CARPETA ─────────────────────────────────────────
    @http.route(
        ['/my/documents/folder/<int:folder_id>',
         '/my/documents/folder/<int:folder_id>/page/<int:page>'],
        type='http', auth='user', website=True
    )
    def portal_folder_documents(self, folder_id, page=1, sortby=None, **kw):
        """
        Muestra los archivos de una carpeta específica para el usuario actual.
        Incluye archivos con folder_id = carpeta (origen) y archivos compartidos
        a esa carpeta (shared_folder_ids).
        """
        user = request.env.user
        Attachment = request.env['ir.attachment'].sudo()
        Folder = request.env['documents.folders'].sudo()
    
        folder = Folder.browse(folder_id)
        if not folder.exists():
            return request.redirect('/my/documents')
    
        domain = [
            '|',
            ('folder_id', '=', folder_id),
            ('shared_folder_ids', 'in', folder_id),
            ('res_model', 'not in', ['ir.ui.view', 'ir.module.module']),
            '|',
            ('create_uid', '=', user.id),
            ('shared_user_ids', 'in', [user.id]),
        ]
    
        searchbar_sortings = {
            'date': {'label': _('Más reciente'), 'order': 'create_date desc, id desc'},
            'name': {'label': _('Nombre'),       'order': 'name asc, id asc'},
        }
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
    
        documents_count = Attachment.search_count(domain)
    
        pager = portal_pager(
            url=f'/my/documents/folder/{folder_id}',
            url_args={'sortby': sortby},
            total=documents_count,
            page=page,
            step=self._items_per_page,
        )
    
        documents = Attachment.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset'],
        )
    
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'documents',
            'folder': folder,
            'documents': documents,
            'pager': pager,
            'sortby': sortby,
            'searchbar_sortings': searchbar_sortings,
            'base_url': request.env['ir.config_parameter'].sudo()
                        .get_param('web.base.url'),
        })
        return request.render(
            'documents_portal_management_extension.portal_folder_documents',
            values,
        )
