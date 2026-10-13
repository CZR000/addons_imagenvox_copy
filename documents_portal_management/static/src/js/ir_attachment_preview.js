/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { BinaryField } from "@web/views/fields/binary/binary_field";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

import { FileViewer } from "@web/core/file_viewer/file_viewer";
import { uniqueId } from "@web/core/utils/functions";
import { registry } from "@web/core/registry";

patch(BinaryField.prototype, {
    setup(...args) {
        super.setup(...args);
        this.store = useService("mail.store");
        this.notification = useService("notification");
    },
    async _onFilePreview(ev){
        ev.preventDefault();
        ev.stopPropagation();
        
        var self = this;

        if(self.props.record.resId){
            try {                
                const viewerId = uniqueId('web.file_viewer');
                const attachment = self.store.Attachment.insert({
                    id: self.props.record.resId,
                    filename: self.props.record.data.name,
                    name: self.props.record.data.name,
                    mimetype: self.props.record.data.mimetype,
                });
                
                var file = self.store.Attachment.get(attachment);
                registry.category("main_components").add(viewerId, {
                    Component: FileViewer,
                    props: {
                        files: [file],
                        startIndex: 0,
                        close: () => {
                            registry.category('main_components').remove(viewerId);
                        },
                    },
                });
            } 
            catch {
                self.notification.add(_t("This file type is not supported."), {
                    type: "danger",
                });
            }
        }else{
            self.notification.add(_t("Something went wrong."), {
                type: "danger",
            });
        }
    },
});
