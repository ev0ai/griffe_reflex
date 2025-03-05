from typing import Dict, Any


def get_radix_mappings(base_dir: str) -> Dict[str, Dict[str, str]]:
    """Get mappings for Radix UI components.
    
    Args:
        base_dir: Base directory of the Reflex codebase
        
    Returns:
        A dictionary of component names to their module paths and file paths.
    """
    return {
        # Radix components
        "accordion": {
            "module_path": "components.radix.primitives.accordion",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/primitives/accordion.py"
        },
        "alert_dialog": {
            "module_path": "components.radix.themes.components.alert_dialog",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/alert_dialog.py"
        },
        "avatar": {
            "module_path": "components.radix.themes.components.avatar",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/avatar.py"
        },
        "badge": {
            "module_path": "components.radix.themes.components.badge",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/badge.py"
        },
        "blockquote": {
            "module_path": "components.radix.themes.typography.blockquote",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/typography/blockquote.py"
        },
        "box": {
            "module_path": "components.radix.themes.layout.box",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/layout/box.py"
        },
        "button": {
            "module_path": "components.radix.themes.components.button",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/button.py"
        },
        "callout": {
            "module_path": "components.radix.themes.components.callout",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/callout.py"
        },
        "card": {
            "module_path": "components.radix.themes.components.card",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/card.py"
        },
        "center": {
            "module_path": "components.radix.themes.layout.center",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/layout/center.py"
        },
        "checkbox": {
            "module_path": "components.radix.themes.components.checkbox",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/checkbox.py"
        },
        "code": {
            "module_path": "components.radix.themes.typography.code",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/typography/code.py"
        },
        "container": {
            "module_path": "components.radix.themes.layout.container",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/layout/container.py"
        },
        "context_menu": {
            "module_path": "components.radix.themes.components.context_menu",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/context_menu.py"
        },
        "data_list": {
            "module_path": "components.radix.themes.components.data_list",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/data_list.py"
        },
        "dialog": {
            "module_path": "components.radix.themes.components.dialog",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/dialog.py"
        },
        "drawer": {
            "module_path": "components.radix.primitives.drawer",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/primitives/drawer.py"
        },
        "dropdown_menu": {
            "module_path": "components.radix.themes.components.dropdown_menu",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/dropdown_menu.py"
        },
        "flex": {
            "module_path": "components.radix.themes.layout.flex",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/layout/flex.py"
        },
        "form": {
            "module_path": "components.radix.primitives.form",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/primitives/form.py"
        },
        "grid": {
            "module_path": "components.radix.themes.layout.grid",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/layout/grid.py"
        },
        "heading": {
            "module_path": "components.radix.themes.typography.heading",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/typography/heading.py"
        },
        "hover_card": {
            "module_path": "components.radix.themes.components.hover_card",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/hover_card.py"
        },
        "input": {
            "module_path": "components.radix.themes.components.text_field",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/text_field.py"
        },
        "inset": {
            "module_path": "components.radix.themes.components.inset",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/inset.py"
        },
        "link": {
            "module_path": "components.radix.themes.typography.link",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/typography/link.py"
        },
        "popover": {
            "module_path": "components.radix.themes.components.popover",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/popover.py"
        },
        "progress": {
            "module_path": "components.radix.themes.components.progress",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/progress.py"
        },
        "radio_group": {
            "module_path": "components.radix.themes.components.radio_group",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/radio_group.py"
        },
        "scroll_area": {
            "module_path": "components.radix.themes.components.scroll_area",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/scroll_area.py"
        },
        "section": {
            "module_path": "components.radix.themes.layout.section",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/layout/section.py"
        },
        "segmented_control": {
            "module_path": "components.radix.themes.components.segmented_control",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/segmented_control.py"
        },
        "select": {
            "module_path": "components.radix.themes.components.select",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/select.py"
        },
        "separator": {
            "module_path": "components.radix.themes.components.separator",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/separator.py"
        },
        "skeleton": {
            "module_path": "components.radix.themes.components.skeleton",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/skeleton.py"
        },
        "slider": {
            "module_path": "components.radix.themes.components.slider",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/slider.py"
        },
        "spacer": {
            "module_path": "components.radix.themes.layout.spacer",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/layout/spacer.py"
        },
        "spinner": {
            "module_path": "components.radix.themes.components.spinner",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/spinner.py"
        },
        "stack": {
            "module_path": "components.radix.themes.layout.stack",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/layout/stack.py"
        },
        "hstack": {
            "module_path": "components.radix.themes.layout.stack",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/layout/stack.py"
        },
        "vstack": {
            "module_path": "components.radix.themes.layout.stack",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/layout/stack.py"
        },
        "switch": {
            "module_path": "components.radix.themes.components.switch",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/switch.py"
        },
        "table": {
            "module_path": "components.radix.themes.components.table",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/table.py"
        },
        "tabs": {
            "module_path": "components.radix.themes.components.tabs",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/tabs.py"
        },
        "text": {
            "module_path": "components.radix.themes.typography.text",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/typography/text.py"
        },
        "text_area": {
            "module_path": "components.radix.themes.components.text_area",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/text_area.py"
        },
        "theme": {
            "module_path": "components.radix.themes.base",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/base.py"
        },
        "tooltip": {
            "module_path": "components.radix.themes.components.tooltip",
            "file_path": f"{base_dir}/reflex/reflex/components/radix/themes/components/tooltip.py"
        }
    } 