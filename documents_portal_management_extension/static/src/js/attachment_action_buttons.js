/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { useFileViewer } from "@web/core/file_viewer/file_viewer_hook";

export class AttachmentActionButtons extends Component {
    static template = "documents_portal_management_extension.AttachmentActionButtons";
    static props = {
        // Props propias del widget
        record: Object,
        // Props estándar que Odoo inyecta en todos los widgets de campo
        id: { type: String, optional: true },
        name: { type: String, optional: true },
        readonly: { type: Boolean, optional: true },
        required: { type: Boolean, optional: true },
        invisible: { type: Boolean, optional: true },
        // Captura cualquier otra prop que Odoo pueda agregar en el futuro
        "*": true,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.fileViewer = useFileViewer();
    }

    onClickPreview() {
        const id = this.props.record.resId;
        const name = this.props.record.data.name || "";
        const mimetype = this.props.record.data.mimetype || "";
        const url = `/web/content/${id}?filename=${encodeURIComponent(name)}`;

        const lowerMimetype = mimetype.toLowerCase();

        const isImage = lowerMimetype.startsWith("image/") || 
                        ["jpg", "jpeg", "png"].some(ext => name.toLowerCase().endsWith(`.${ext}`));

        const file = {
            id,
            displayName: name,
            downloadUrl: url,
            defaultSource: url,
            mimetype: lowerMimetype,
            isViewable: lowerMimetype === "application/pdf" || isImage,
            isImage: isImage,
            isPdf: lowerMimetype === "application/pdf",
            isText: lowerMimetype.startsWith("text/"),
            isVideo: lowerMimetype.startsWith("video/"),
        };

        this.fileViewer.open(file, [file]);
    }

    async onClickEdit() {
        const input = document.createElement("input");
        input.type = "file";
        input.style.display = "none";
        document.body.appendChild(input);

        input.onchange = async (event) => {
            const file = event.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = async (e) => {
                const base64 = e.target.result.split(",")[1];
                const id = this.props.record.resId;

                try {
                    await this.orm.call(
                        "ir.attachment",
                        "action_replace_file",
                        [[id], base64, file.name]
                    );

                    this.notification.add("Archivo actualizado correctamente", {
                        type: "success",
                    });

                    await this.props.record.model.load();

                } catch (error) {
                    this.notification.add("Error al actualizar el archivo", {
                        type: "danger",
                    });
                }
            };
            reader.readAsDataURL(file);
            document.body.removeChild(input);
        };

        input.click();
    }
}

registry.category("fields").add("attachment_action_buttons", {
    component: AttachmentActionButtons,
    supportedTypes: ["integer"],
});