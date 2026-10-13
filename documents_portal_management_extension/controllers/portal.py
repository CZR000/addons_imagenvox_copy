# -*- coding: utf-8 -*-
import base64
import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError

# IMPORTAR EL CONTROLADOR ORIGINAL DEL MÓDULO BASE
from odoo.addons.documents_portal_management.controllers.main import IrAttachemntsShareController

_logger = logging.getLogger(__name__)


class IrAttachmentShareControllerExtension(IrAttachemntsShareController):
    """
    HEREDA del controlador base para sobrescribir el método de descarga
    """
    
    @http.route('/web/get_attachments_data', type='http', auth="user")
    def get_attachments_data(self, id, **kwargs):
        """
        SOBRESCRIBE el método original para soportar URLs y validación de compartidos
        """
        try:
            # 1. Buscar el attachment
            ir_attachment = request.env['ir.attachment'].sudo().browse(int(id))
            
            if not ir_attachment.exists():
                _logger.warning(f"Documento ID {id} no existe")
                return request.render('http_routing.404')
            
            # 2. Validación de acceso
            user = request.env.user
            is_accessible = False
            
            # Validación 1: Es el creador
            if user.id == ir_attachment.create_uid.id:
                is_accessible = True
                _logger.info(f"✅ Acceso: {user.name} es creador de '{ir_attachment.name}'")
            
            # Validación 2: Está compartido explícitamente
            elif user.id in ir_attachment.shared_user_ids.ids:
                is_accessible = True
                _logger.info(f"✅ Acceso: {user.name} en shared_user_ids de '{ir_attachment.name}'")
            
            # Validación 3: Está en su carpeta personal (usuarios portal)
            elif hasattr(user, 'portal_folder_id') and user.portal_folder_id:
                if ir_attachment.folder_id.id == user.portal_folder_id.id:
                    is_accessible = True
                    _logger.info(f"✅ Acceso: {user.name} accede a su carpeta personal")
            
            if not is_accessible:
                _logger.warning(
                    f"❌ ACCESO DENEGADO: Usuario '{user.name}' (ID:{user.id}) "
                    f"intentó acceder a '{ir_attachment.name}' (ID:{id}). "
                    f"Creador: {ir_attachment.create_uid.name}, "
                    f"Compartido con: {ir_attachment.shared_user_ids.mapped('name')}, "
                    f"Carpeta: {ir_attachment.folder_id.name if ir_attachment.folder_id else 'N/A'}"
                )
                return request.render('http_routing.404')
            
            # 3. CASO 1: Es una URL (type='url')
            if ir_attachment.type == 'url':
                url = ir_attachment.url
                
                if not url:
                    _logger.error(f"❌ Documento '{ir_attachment.name}' es tipo URL pero no tiene URL definida")
                    return request.render('http_routing.404')
                
                # Asegurar que tenga protocolo
                if not url.startswith(('http://', 'https://', 'ftp://')):
                    url = 'https://' + url
                
                _logger.info(f"🔗 REDIRECCIÓN: {user.name} → {url}")
                
                # USAR WERKZEUG REDIRECT DIRECTO
                import werkzeug.utils
                return werkzeug.utils.redirect(url, code=302)
            
            # 4. CASO 2: Es un archivo binario (type='binary')
            if not ir_attachment.datas:
                _logger.error(f"❌ Documento '{ir_attachment.name}' no tiene contenido binario")
                return request.render('http_routing.404')
            
            try:
                content = base64.b64decode(ir_attachment.datas)
            except Exception as decode_error:
                _logger.error(f"❌ Error decodificando base64 para '{ir_attachment.name}': {str(decode_error)}")
                return request.render('http_routing.404')
            
            filename = ir_attachment.name or 'attachment'
            mimetype = ir_attachment.mimetype or 'application/octet-stream'
            
            _logger.info(f"📥 DESCARGA: {user.name} descarga '{filename}' ({len(content)} bytes)")
            
            return request.make_response(
                content,
                headers=[
                    ('Content-Type', mimetype),
                    ('Content-Disposition', f'attachment; filename="{filename}"'),
                    ('Content-Length', str(len(content))),
                ]
            )
            
        except ValueError as e:
            _logger.error(f"❌ ID inválido: {id} - {str(e)}")
            return request.render('http_routing.404')
        except Exception as e:
            _logger.exception(f"❌ Error inesperado procesando documento ID {id}")
            return request.render('http_routing.404')


class DocumentPortalExtension(http.Controller):
    """
    Controlador para funcionalidades adicionales del portal
    """
    
    # -------------------------------------------------------------------------
    # REQUERIMIENTO: Agregar links desde el portal
    # -------------------------------------------------------------------------
    @http.route(
        ['/my/documents/add_link'],
        type='http',
        auth='user',
        website=True,
    )
    def portal_add_link_form(self, **kw):
        """
        Muestra el formulario para agregar un link externo (URL)
        como documento en la carpeta personal del usuario portal.
        """
        if not request.session.uid:
            return request.redirect('/web/login')
        values = {
            'page_name': 'add_link',
            'error': kw.get('error', ''),
        }
        return request.render(
            'document_portal_management_extension.portal_add_link_form',
            values,
        )
    
    @http.route(
        ['/my/documents/add_link/save'],
        type='http',
        auth='user',
        methods=['POST'],
        website=True,
    )
    def portal_add_link_save(self, **post):
        """
        Recibe el POST del formulario de link, valida y crea el ir.attachment
        de tipo 'url' en la carpeta personal del usuario portal.
        """
        user = request.env.user
        user_sudo = request.env['res.users'].sudo().browse(user.id)
        name = post.get('link_name', '').strip()
        url  = post.get('link_url', '').strip()
        
        # Validaciones basicas
        if not name:
            return request.redirect('/my/documents/add_link?error=name')
        if not url:
            return request.redirect('/my/documents/add_link?error=url')
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Carpeta destino: la carpeta personal del usuario portal
        target_folder_id = user_sudo.portal_folder_id.id
        
        # Si no tiene carpeta asignada intentamos crearla
        if not target_folder_id and user_sudo.share:
            try:
                user_sudo._ensure_portal_folder_exists()
                target_folder_id = user_sudo.portal_folder_id.id
            except Exception as e:
                _logger.error(
                    "No se pudo crear carpeta para %s: %s", user.name, e
                )
        
        # Fallback a carpeta raiz portal
        if not target_folder_id:
            portal_dir = request.env.ref(
                'documents_portal_management.portal_folder',
                raise_if_not_found=False,
            )
            target_folder_id = portal_dir.id if portal_dir else False
        
        try:
            request.env['ir.attachment'].sudo().create({
                'name': name,
                'type': 'url',
                'url': url,
                'folder_id': target_folder_id,
                'res_model': 'res.users',
                'res_id': user.id,
                'partner_id': user_sudo.partner_id.id,
            })
        except ValidationError as e:
            return json.dumps({'error_fields': e.args[0]})
        except Exception as e:
            _logger.exception("Error guardando link portal")
            return json.dumps({
                'Error': _('No se pudo guardar el link. Detalle: %s') % str(e)
            })
        
        return request.redirect('/my/documents')