/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.IrAttachmentDownload = publicWidget.Widget.extend({
    selector: '.portal-attachment-download .fa-download',
    events: { 'click': '_onclick' },

    async _onclick(ev) {
        ev.preventDefault();
        const attachmentId = this.$el.data('attachment-id');
        if (!attachmentId) {
            console.error("Attachment ID not found.");
            return;
        }
        const downloadUrl = `/web/get_attachments_data?id=${attachmentId}`;
        window.location.href = downloadUrl;
    },
});
