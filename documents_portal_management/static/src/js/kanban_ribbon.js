/** @odoo-module */

import { _lt, _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

import { Component } from "@odoo/owl";

class WebKanbanRibbonWidget extends Component {
    static template = "documents_portal_management.kanban_ribbon";
    static props = {
        ...standardWidgetProps,
        text: { type: String },
        icon : { type: String, optional: true },
        bg_color: { type: String, optional: true },
    };
    static defaultProps = {
        bg_color: "text-bg-success",
    };

    get classes() {
        let classes = this.props.bg_color;
        classes += " content";
        if (this.props.text && this.props.text.length > 15) {
            classes += " o_small";
        } 
        else if (this.props.text && this.props.text.length > 10) {
            classes += " o_medium";
        }
        return classes;
    }    
}

export const WebKanbanRibbonWidgetField = {
    component: WebKanbanRibbonWidget,
    extractProps: ({ attrs }) => {
        return {
            text: attrs.title || attrs.text,
            icon: attrs.icon,
            bg_color: attrs.bg_color,
        };
    },
};
registry.category("view_widgets").add("kanban_ribbon", WebKanbanRibbonWidgetField);
