"""
Writer module for saving specification files.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List

# Constants
COMMON_PROP_CATEGORIES = {
    "layout_props": ["width", "height", "min_width", "max_width", "min_height", "max_height", "padding", "padding_x", "padding_y", "padding_top", "padding_right", "padding_bottom", "padding_left"],
    "position_props": ["position", "top", "right", "bottom", "left", "z_index"],
    "flex_props": ["flex", "flex_grow", "flex_shrink", "flex_basis", "justify_content", "align_items", "align_content", "align_self", "order"],
    "grid_props": ["grid_template_columns", "grid_template_rows", "grid_template_areas", "grid_column", "grid_row", "grid_area", "grid_auto_flow", "grid_auto_rows", "grid_auto_columns", "gap", "row_gap", "column_gap"],
    "spacing_props": ["margin", "margin_top", "margin_right", "margin_bottom", "margin_left", "margin_x", "margin_y"],
    "border_props": ["border", "border_width", "border_style", "border_color", "border_top", "border_right", "border_bottom", "border_left", "border_radius"],
    "shadow_props": ["box_shadow", "text_shadow"],
    "color_props": ["color", "background", "background_color", "opacity"],
    "typography_props": ["font_family", "font_size", "font_weight", "line_height", "text_align", "font_style", "text_decoration", "text_transform", "letter_spacing"],
}

# Type mappings with enum values
TYPE_MAPPINGS = {
    "LiteralRadius": {
        "values": ["none", "small", "medium", "large", "full"]
    },
    "LiteralButtonSize": {
        "values": ["1", "2", "3", "4"]
    },
    "LiteralVariant": {
        "values": ["solid", "soft", "outline", "ghost"]
    },
    "LiteralAccentColor": {
        "values": ["gray", "tomato", "red", "ruby", "crimson", "pink", "plum", "purple", "violet", "iris", "indigo", "blue", "cyan", "teal", "jade", "green", "grass", "brown", "orange", "sky", "mint", "lime", "yellow", "amber", "gold", "bronze"]
    },
    "LiteralAccordionType": {
        "values": ["single", "multiple"]
    },
    "LiteralAccordionDir": {
        "values": ["ltr", "rtl"]
    },
    "LiteralAccordionOrientation": {
        "values": ["vertical", "horizontal"]
    }
}

def create_empty_spec(component_name: str, mapping: Dict[str, str]) -> Dict[str, Any]:
    """Create an empty spec for a component.
    
    Args:
        component_name: The name of the component
        mapping: The mapping information for the component
        
    Returns:
        An empty spec dictionary
    """
    return {
        "name": component_name,
        "module_path": mapping.get('module_path', ''),
        "file_path": mapping.get('file_path', ''),
        "docstring": "",
        "bases": [],
        "properties": [],
        "event_names": [],
        "enum_values": {},
        "styling_properties": {},
        "subcomponents": {}
    }

def save_spec_file(spec: Dict[str, Any], component_name: str, specs_dir: str) -> str:
    """Save a spec to a file.
    
    Args:
        spec: The specification dictionary
        component_name: The name of the component
        specs_dir: The directory to save the spec to
        
    Returns:
        The path to the saved spec file
    """
    # Skip invalid component names
    invalid_components = ["component", "next_link", "nextlink", "nossrcomponent"]
    if component_name.lower() in invalid_components:
        print(f"Skipping invalid component: {component_name}")
        return ""
    
    # Sanitize component name for the filename
    sanitized_name = component_name.replace(" ", "_")
    spec_path = os.path.join(specs_dir, f"{sanitized_name}.json")
    os.makedirs(os.path.dirname(spec_path), exist_ok=True)
    
    with open(spec_path, "w") as f:
        json.dump(spec, f, indent=2)
    
    return spec_path

def generate_common_props_spec(specs_dir: str = 'specs', common_event_handlers: List[str] = None) -> Dict[str, Any]:
    """Generate a compact spec file for common properties.
    
    Args:
        specs_dir: The directory to save the spec to
        common_event_handlers: List of common event handler names
        
    Returns:
        The common props specification dictionary
    """
    if common_event_handlers is None:
        from spec_generator.extraction import COMMON_EVENT_HANDLERS
        common_event_handlers = COMMON_EVENT_HANDLERS
    
    common_props_spec = {
        "name": "common_props",
        "description": "Common properties shared by most Reflex components",
        "events": common_event_handlers,  # List of event names
        "categories": {}
    }
    
    # Add common prop categories
    for category, props in COMMON_PROP_CATEGORIES.items():
        category_name = f"{category}_props"
        common_props_spec["categories"][category_name] = {
            "description": f"Common {category} props",
            "props": props  # List of property names
        }
    
    # Add type mappings with enum values
    common_props_spec["type_mappings"] = TYPE_MAPPINGS
    
    # Save the common props spec
    spec_path = os.path.join(specs_dir, "common_props.json")
    os.makedirs(os.path.dirname(spec_path), exist_ok=True)
    
    with open(spec_path, 'w') as f:
        json.dump(common_props_spec, f, indent=2)
    
    print(f"Common props spec file saved to: {os.path.abspath(spec_path)}")
    
    return common_props_spec

def generate_spec_files(base_dir: str = None, specs_dir: str = 'specs') -> None:
    """Generate spec files for all components.
    
    Args:
        base_dir: The base directory of the Reflex codebase
        specs_dir: The directory to save specs to
    """
    if base_dir is None:
        base_dir = os.getcwd()
    
    print("Generating specification files...")
    
    # Generate common props spec
    common_props_spec = generate_common_props_spec(specs_dir)
    
    # Find all components in the codebase
    from spec_generator.discovery import find_all_components
    component_mappings = find_all_components(base_dir)
    
    # Generate spec files for each component
    success_count = 0
    failure_count = 0
    processed = 0
    
    for component_name, mapping in component_mappings.items():
        processed += 1
        print(f"Processing component: {component_name}")
        print(f"  Module path: {mapping['module_path']}")
        print(f"  File path: {mapping['file_path']}")
        
        # Skip components that don't have a file path
        if not os.path.exists(mapping['file_path']):
            print(f"  Warning: File {mapping['file_path']} does not exist")
            spec = create_empty_spec(component_name, mapping)
            
            # Save spec to file
            spec_path = save_spec_file(spec, component_name, specs_dir)
            print(f"  Spec file saved to: {spec_path}")
            failure_count += 1
            continue
        
        # Extract component information
        try:
            from spec_generator.extraction import extract_component_info
            spec = extract_component_info(component_name, mapping, None)
            
            # Save spec to file
            spec_path = save_spec_file(spec, component_name, specs_dir)
            print(f"  Spec file saved to: {spec_path}")
            success_count += 1
            
            if "error" in spec:
                failure_count += 1
        except Exception as e:
            print(f"  Error extracting component info: {str(e)}")
            failure_count += 1
    
    print(f"\nProcessed {processed} components with {failure_count} failures")
    print(f"Spec files saved to: {os.path.abspath(specs_dir)}") 