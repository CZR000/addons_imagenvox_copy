/** @odoo-module */

import { FormRenderer } from '@web/views/form/form_renderer';
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

const { onMounted, onPatched, useEnv } = owl;

patch(FormRenderer.prototype, {
    setup(...args) {
        super.setup(...args);
        this.action = useService("action");
        onPatched(this._renderShareButton.bind(this));
        onMounted(this._renderShareButton.bind(this));
    },

    _renderShareButton() {
        if (this.props.record.resModel === 'ir.attachment') {
            const shareButtonDiv = document.createElement('div');
            shareButtonDiv.classList.add('attachment_share_button');

            const shareButton = document.createElement('button');
            shareButton.classList.add('btn', 'btn-primary');

            const shareIcon = document.createElement('i');
            shareIcon.classList.add('fa', 'fa-share-alt');
            shareButton.appendChild(shareIcon);

            shareButtonDiv.appendChild(shareButton);
            shareButton.addEventListener('click', this._clickShareButton.bind(this));

            const formSheet = document.querySelector('.o_form_sheet');
            if (this.props.record.resId && this.props.record.data.datas && formSheet) {
                formSheet.appendChild(shareButtonDiv);
            }
        }
    },
    
    _clickShareButton: function(ev) {
        ev.stopPropagation();
        ev.preventDefault();            
        var self = this;
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: _t('Share Attachments'),
            res_model: 'ir.attachment.share',
            views: [[false, 'form']],
            view_mode: 'form',
            target: 'new',
            context: {
                active_model : self.props.record.resModel || false,
                default_res_id : self.props.record.resId || false,
                active_id : self.props.record.resId || false,
            }
        })
    },
})

export default FormRenderer;