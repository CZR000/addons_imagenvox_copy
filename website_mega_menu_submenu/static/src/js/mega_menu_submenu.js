/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Widget para manejar interacciones avanzadas en mega menú con submenús
 */
publicWidget.registry.MegaMenuSubmenu = publicWidget.Widget.extend({
    selector: '.o_mega_menu',
    events: {
        'mouseenter .mega-menu-sub-item': '_onSubmenuItemEnter',
        'mouseleave .mega-menu-sub-item': '_onSubmenuItemLeave',
        'click .mega-menu-sub-item': '_onSubmenuItemClick',
    },
    
    /**
     * Inicialización del widget
     */
    start: function () {
        this._super.apply(this, arguments);
        this._setupAnimations();
        this._setupAccessibility();
        this._preloadImages();
        return this._super(...arguments);
    },
    
    /**
     * Configurar animaciones de entrada
     */
    _setupAnimations: function () {
        const items = this.el.querySelectorAll('.mega-menu-item-container');
        
        // Observer para animaciones cuando el mega menú se hace visible
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');
                }
            });
        }, {
            threshold: 0.1
        });
        
        items.forEach(item => {
            observer.observe(item);
        });
    },
    
    /**
     * Mejorar accesibilidad (ARIA labels, keyboard navigation)
     */
    _setupAccessibility: function () {
        const parentItems = this.el.querySelectorAll('.mega-menu-parent-item');
        const subItems = this.el.querySelectorAll('.mega-menu-sub-item');
        
        // Agregar roles ARIA
        parentItems.forEach(item => {
            item.setAttribute('role', 'heading');
            item.setAttribute('aria-level', '3');
        });
        
        subItems.forEach(item => {
            item.setAttribute('role', 'menuitem');
            item.setAttribute('tabindex', '0');
            
            // Soporte para navegación con teclado
            item.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    item.click();
                }
            });
        });
    },
    
    /**
     * Precargar imágenes de íconos si las hay
     */
    _preloadImages: function () {
        const icons = this.el.querySelectorAll('.mega-menu-item-container i');
        // Aquí podrías agregar lógica para precargar íconos personalizados
    },
    
    /**
     * Handler: Mouse entra en un sub-item
     */
    _onSubmenuItemEnter: function (ev) {
        const $item = $(ev.currentTarget);
        
        // Agregar clase de hover con delay
        setTimeout(() => {
            if ($item.is(':hover')) {
                $item.addClass('is-hovered');
            }
        }, 100);
        
        // Efecto ripple (opcional)
        this._createRipple(ev);
    },
    
    /**
     * Handler: Mouse sale de un sub-item
     */
    _onSubmenuItemLeave: function (ev) {
        const $item = $(ev.currentTarget);
        $item.removeClass('is-hovered');
    },
    
    /**
     * Handler: Click en un sub-item
     */
    _onSubmenuItemClick: function (ev) {
        const $item = $(ev.currentTarget);
        const href = $item.attr('href');
        
        // Analytics tracking (si está disponible)
        if (typeof gtag !== 'undefined') {
            gtag('event', 'mega_menu_click', {
                'event_category': 'navigation',
                'event_label': $item.text().trim(),
                'value': href
            });
        }
        
        // Animación de salida antes de navegar
        if (!ev.ctrlKey && !ev.metaKey && $item.attr('target') !== '_blank') {
            ev.preventDefault();
            $item.addClass('clicked');
            
            setTimeout(() => {
                window.location.href = href;
            }, 200);
        }
    },
    
    /**
     * Crear efecto ripple al hacer hover
     */
    _createRipple: function (ev) {
        const $item = $(ev.currentTarget);
        
        // Evitar múltiples ripples
        if ($item.find('.ripple').length > 0) {
            return;
        }
        
        const $ripple = $('<span class="ripple"></span>');
        const rect = ev.currentTarget.getBoundingClientRect();
        const x = ev.clientX - rect.left;
        const y = ev.clientY - rect.top;
        
        $ripple.css({
            left: x + 'px',
            top: y + 'px',
            position: 'absolute',
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            background: 'rgba(197, 86, 17, 0.3)',
            transform: 'scale(0)',
            animation: 'ripple-animation 0.6s ease-out',
            pointerEvents: 'none'
        });
        
        $item.css('position', 'relative');
        $item.append($ripple);
        
        setTimeout(() => {
            $ripple.remove();
        }, 600);
    },
    
    /**
     * Cleanup al destruir el widget
     */
    destroy: function () {
        // Limpiar event listeners adicionales si los hay
        this._super.apply(this, arguments);
    }
});

// CSS para animación ripple (inyectado dinámicamente)
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple-animation {
            to {
                transform: scale(20);
                opacity: 0;
            }
        }
        
        .mega-menu-sub-item.clicked {
            transform: scale(0.95);
        }
    `;
    document.head.appendChild(style);
}

export default publicWidget.registry.MegaMenuSubmenu;