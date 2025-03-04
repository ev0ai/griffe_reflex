#!/usr/bin/env python
"""
Script to generate spec files for Reflex components using Griffe.

This script will:
1. Scan through the Reflex library documentation directories
2. Map each documented component to its corresponding source file
3. Extract component information including:
   - Properties (styling, events, general)
   - Methods
   - Base classes
4. Generate JSON spec files for each component in the specs directory
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple

import griffe

print(f"Griffe version: {griffe.__version__ if hasattr(griffe, '__version__') else 'unknown'}")

# Paths
REFLEX_ROOT = Path('/Users/dave/code/griffe_reflex/reflex')
REFLEX_LIB_DOC_DIR = REFLEX_ROOT / 'docs' / 'library'
REFLEX_COMPONENTS_DIR = REFLEX_ROOT / 'reflex' / 'components'
SPECS_DIR = Path('/Users/dave/code/griffe_reflex/specs')

# Ensure specs directory exists
SPECS_DIR.mkdir(exist_ok=True)

# Load the __init__.py file to extract component mappings
init_path = REFLEX_ROOT / 'reflex' / '__init__.py'
pyi_path = REFLEX_ROOT / 'reflex' / '__init__.pyi'

# Common Reflex event handlers that should be included in all component specs
COMMON_EVENT_HANDLERS = [
    "on_blur", "on_click", "on_context_menu", "on_double_click", "on_focus",
    "on_mount", "on_mouse_down", "on_mouse_enter", "on_mouse_leave", "on_mouse_move",
    "on_mouse_out", "on_mouse_over", "on_mouse_up", "on_scroll", "on_unmount"
]

# Common prop sets
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

# Modify TYPE_MAPPINGS to be much simpler
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

# Add function to parse enum values from descriptions
def extract_enum_values_from_description(description):
    """Extract enum values from description strings like 'Options: "value1" | "value2" | "value3"'"""
    # Find patterns like "value1" | "value2" | "value3"
    enum_match = re.search(r'(?:"([^"]+)"(?:\s*\|\s*"([^"]+)")+)', description)
    if enum_match:
        # Extract all double-quoted values
        values = re.findall(r'"([^"]+)"', description)
        return values
    return None

def print_debug(*args, **kwargs):
    """Debug print function."""
    # Uncomment to enable debug printing
    # print(*args, **kwargs)
    pass

def extract_component_mappings(base_dir):
    """Extract component mappings from reflex/reflex/components/__init__.pyi.
    
    Returns a dictionary of component names to their module paths and file paths.
    """
    mappings = {}
    
    # Get the path to the __init__.pyi file which contains component imports
    init_file = f"{base_dir}/reflex/reflex/components/__init__.pyi"
    
    # Regular expression to match import statements
    import_pattern = re.compile(r'from\s+\.([a-zA-Z0-9_.]+)\s+import\s+([a-zA-Z0-9_,\s]+)')
    
    # Check if the file exists
    if not os.path.exists(init_file):
        print(f"Warning: Could not find {init_file}")
        return mappings
    
    # Read the file and extract imports
    with open(init_file, 'r') as f:
        for line in f:
            match = import_pattern.match(line.strip())
            if match:
                module_path = match.group(1)
                imported = match.group(2).split(',')
                for item in imported:
                    component_name = item.strip().lower()
                    if component_name and component_name != "component":
                        file_path = f"{base_dir}/reflex/reflex/components/{module_path.replace('.', '/')}.py"
                        mappings[component_name] = {
                            "module_path": f"components.{module_path}",
                            "file_path": file_path
                        }
    
    return mappings

def scan_library_docs() -> Dict[str, Path]:
    """
    Scan the Reflex library documentation directories to find documented components.
    
    Returns a mapping of component names to their documentation file paths.
    """
    component_to_doc_path = {}
    
    # Walk through the library documentation directory
    for root, dirs, files in os.walk(REFLEX_LIB_DOC_DIR):
        for file in files:
            if file.endswith('.md'):
                doc_path = Path(root) / file
                
                # Read the file to extract component info from frontmatter
                with open(doc_path, 'r') as f:
                    content = f.read()
                
                # Extract component names from frontmatter
                frontmatter_match = re.search(r'---\s+(.*?)\s+---', content, re.DOTALL)
                if frontmatter_match:
                    frontmatter = frontmatter_match.group(1)
                    components_match = re.search(r'components:\s*\n((?:\s*-\s*.*\n)+)', frontmatter)
                    
                    if components_match:
                        components_lines = components_match.group(1)
                        for line in components_lines.strip().split('\n'):
                            component_match = re.search(r'-\s*(rx\.[a-zA-Z_]+)', line.strip())
                            if component_match:
                                component_name = component_match.group(1).replace('rx.', '')
                                component_to_doc_path[component_name] = doc_path
    
    return component_to_doc_path

def extract_component_info(component_name: str, component_data: Dict[str, str], doc_path: Path) -> Dict[str, Any]:
    """
    Extract component information from a file.
    
    Args:
        component_name: The name of the component.
        component_data: The component data from the mappings.
        doc_path: The path to the documentation file.
    
    Returns:
        A dictionary with the component information.
    """
    module_path = component_data['module_path']
    module_name = module_path.split('.')[-1]
    file_path = component_data['file_path']
    
    # Create the base spec
    spec = {
        "name": component_name,
        "module_path": module_path,
        "module_name": module_name,
        "file_path": str(file_path),
        "doc_path": str(doc_path) if doc_path else None,
        "docstring": "",
        "bases": [],
        "supports_common_props": False,  # Will be set to True for components that support common props
        "properties": [],
        "event_names": [],  # Change from 'events' to 'event_names' - just a list of names
        "styling_props": [],
        "subcomponents": {}  # New field to store subcomponent specs
    }
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"  Warning: File {file_path} does not exist")
        spec["error"] = f"File not found: {file_path}"
        return spec
    
    # Extract information from the file
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for both the exact module name and a capitalized version
        class_names_to_try = [
            module_name,  # Original name
            module_name.capitalize(),  # Capitalized (first letter only)
            ''.join(word.capitalize() for word in module_name.split('_')),  # CamelCase
            module_name.upper()  # ALL_CAPS
        ]
        
        class_match = None
        class_name = None
        
        # Try different class name patterns
        for name in class_names_to_try:
            class_pattern = rf"class\s+{name}\b[^:]*:"
            class_match = re.search(class_pattern, content)
            if class_match:
                class_name = name
                print(f"  Found class {class_name}")
                break
        
        # If still not found, look for any class with a create method
        if not class_match:
            create_pattern = r"class\s+(\w+)[^:]*:.*?\n\s+@classmethod\s+def\s+create\s*\("
            create_match = re.search(create_pattern, content, re.DOTALL)
            
            if create_match:
                class_name = create_match.group(1)
                print(f"  Found class {class_name} with create method")
                class_pattern = rf"class\s+{class_name}\b[^:]*:"
                class_match = re.search(class_pattern, content)
        
        if class_match:
            # Extract the entire class definition
            class_start = class_match.start()
            
            # Find the class body by balancing braces and indentation
            class_body = ""
            open_braces = 0
            in_class = True
            line_start = content.rfind('\n', 0, class_start) + 1
            
            for i in range(class_start, len(content)):
                if content[i] == '{':
                    open_braces += 1
                elif content[i] == '}':
                    open_braces -= 1
                elif content[i] == '\n':
                    # Check if next line is part of the class (has indentation)
                    next_line_start = i + 1
                    if next_line_start < len(content):
                        # If we're out of braces and the next line is not indented, we're out of the class
                        if open_braces == 0 and next_line_start < len(content) and not content[next_line_start].isspace():
                            in_class = False
                
                if not in_class and open_braces == 0:
                    class_body = content[class_start:i]
                    break
            
            if not class_body:
                class_body = content[class_start:]
            
            # Extract docstring
            docstring_match = re.search(r'"""(.*?)"""', class_body, re.DOTALL)
            if docstring_match:
                spec["docstring"] = docstring_match.group(1).strip()
            
            # Extract base classes
            bases_match = re.search(rf"class\s+{class_name}\s*\((.*?)\)\s*:", class_body)
            if bases_match:
                bases = bases_match.group(1)
                spec["bases"] = [base.strip() for base in bases.split(',')]
            
            # Check if component supports common prop categories
            supports_common_props = False
            for base in spec["bases"]:
                if any(common_base in base for common_base in ["Component", "Element", "Box", "Div", "Link"]):
                    supports_common_props = True
                    break
            
            spec["supports_common_props"] = supports_common_props
            
            # Add standard event handlers if component supports common props - just the names
            if supports_common_props and not spec.get('error'):
                for event_name in COMMON_EVENT_HANDLERS:
                    # Check if event already exists
                    if event_name not in spec["event_names"]:
                        spec["event_names"].append(event_name)
            
            # Check if this is a ComponentNamespace or contains other component classes
            if "ComponentNamespace" in spec["bases"]:
                print(f"  This is a ComponentNamespace, looking for member components...")
                
                # Extract subcomponent class names
                subcomponent_pattern = r"(\w+)\s*=\s*staticmethod\((\w+)\.create\)"
                subcomponents = re.finditer(subcomponent_pattern, class_body, re.MULTILINE)
                
                subcomponent_classes = []
                for sc_match in subcomponents:
                    subcomponent_classes.append(sc_match.group(2))
                
                if subcomponent_classes:
                    print(f"  Found subcomponents: {', '.join(subcomponent_classes)}")
                    
                    # Look for each subcomponent class and extract its properties
                    for sc_class in subcomponent_classes:
                        sc_pattern = rf"class\s+{sc_class}\b[^:]*:"
                        sc_match = re.search(sc_pattern, content)
                        
                        if sc_match:
                            print(f"  Extracting info from {sc_class}")
                            sc_start = sc_match.start()
                            
                            # Find the subcomponent class body
                            sc_body = ""
                            sc_open_braces = 0
                            sc_in_class = True
                            sc_line_start = content.rfind('\n', 0, sc_start) + 1
                            
                            for i in range(sc_start, len(content)):
                                if content[i] == '{':
                                    sc_open_braces += 1
                                elif content[i] == '}':
                                    sc_open_braces -= 1
                                elif content[i] == '\n':
                                    next_line_start = i + 1
                                    if next_line_start < len(content):
                                        if sc_open_braces == 0 and next_line_start < len(content) and not content[next_line_start].isspace():
                                            sc_in_class = False
                                
                                if not sc_in_class and sc_open_braces == 0:
                                    sc_body = content[sc_start:i]
                                    break
                            
                            if not sc_body:
                                sc_body = content[sc_start:]
                            
                            # Extract subcomponent base classes to check if it supports common props
                            sc_bases_match = re.search(rf"class\s+{sc_class}\s*\((.*?)\)\s*:", sc_body)
                            sc_bases = []
                            supports_common_props = False
                            
                            if sc_bases_match:
                                sc_bases = [base.strip() for base in sc_bases_match.group(1).split(',')]
                                for base in sc_bases:
                                    if any(common_base in base for common_base in ["Component", "Element", "RadixThemesComponent", "HTMLElement"]):
                                        supports_common_props = True
                                        break
                            
                            # Extract subcomponent docstring
                            sc_docstring = ""
                            sc_docstring_match = re.search(r'"""(.*?)"""', sc_body, re.DOTALL)
                            if sc_docstring_match:
                                sc_docstring = sc_docstring_match.group(1).strip()
                            
                            # Create a subcomponent spec
                            sc_spec = {
                                "name": sc_class,
                                "docstring": sc_docstring,
                                "bases": sc_bases,
                                "supports_common_props": supports_common_props,
                                "properties": [],
                                "event_names": [],
                                "styling_props": []
                            }
                            
                            # Add common event handlers if this component supports common props
                            if supports_common_props:
                                for event_name in COMMON_EVENT_HANDLERS:
                                    sc_spec["event_names"].append(event_name)
                            
                            # Extract properties from the subcomponent
                            extract_properties_from_class_body(sc_body, sc_spec)
                            
                            # Add the subcomponent spec to the main spec
                            spec["subcomponents"][sc_class] = sc_spec
            
            # Extract properties from the main component class
            extract_properties_from_class_body(class_body, spec)
        
        else:
            print(f"  Warning: No suitable class found in {file_path}")
            spec["error"] = f"No suitable class found"
    
    except Exception as e:
        print(f"  Error extracting info from file {file_path}: {e}")
        spec["error"] = f"Failed to extract component info: {str(e)}"
    
    return spec

def extract_properties_from_class_body(class_body, spec, class_prefix=None):
    """Extract properties from a class body."""
    
    def should_skip_property(name):
        """Check if a property should be skipped."""
        # Skip special methods and internal attributes
        if name.startswith('__') or name.startswith('_') or name == 'tag':
            return True
        
        # Skip method parameters like "Returns", "Args", "Parameters"
        if name in ['Returns', 'Args', 'Parameters', 'Example', 'Examples', 'Note', 'Notes', 'Raises']:
            return True
        
        # Skip other internal attributes
        internal_attrs = ['children', 'component_name', 'lib', 'lib_dependencies', 'alias']
        if name in internal_attrs:
            return True
        
        return False
    
    # Define patterns for matching properties and methods
    property_pattern = re.compile(r'(?:^|\n)\s*([\w]+)\s*(?::|=)', re.MULTILINE)
    
    # Identify method definitions to avoid capturing their parameters as properties
    method_pattern = re.compile(r'(?:^|\n)\s*def\s+([\w_]+)\s*\(', re.MULTILINE)
    method_sections = []
    
    # Find all method definitions and mark their sections
    for method_match in re.finditer(method_pattern, class_body):
        method_name = method_match.group(1)
        method_start = method_match.start()
        
        # Find the end of the method by tracking indentation
        lines = class_body[method_start:].split('\n')
        method_end = method_start
        method_indent = None
        
        for i, line in enumerate(lines):
            if i == 0:
                # First line defines the method, get its indentation level
                method_indent = len(line) - len(line.lstrip())
                continue
                
            line_stripped = line.lstrip()
            if not line_stripped:  # Skip empty lines
                continue
                
            current_indent = len(line) - len(line_stripped)
            
            # If we find a line with same or less indentation than the method definition,
            # we've reached the end of the method
            if current_indent <= method_indent:
                method_end += len('\n'.join(lines[:i]))
                break
        
        # If we didn't find the end, assume it goes to the end of the class
        if method_end == method_start:
            method_end = len(class_body)
        
        method_sections.append((method_start, method_end))
    
    # First get class attributes with type annotations
    type_pattern = re.compile(r'(?:^|\n)\s*([\w]+)\s*:\s*([^=\n]+)(?:=|$|\n)', re.MULTILINE)
    for match in re.finditer(type_pattern, class_body):
        name = match.group(1)
        if should_skip_property(name):
            continue
        
        # Skip if property is in a method section
        if any(start <= match.start() <= end for start, end in method_sections):
            continue
        
        # Check if this is a property or an event handler
        is_event = name.startswith('on_')
        
        # Get the type annotation
        type_annotation = match.group(2).strip()
        
        # Extract docstring or comment
        docstring = ''
        
        # Look for a docstring in triple quotes after the property
        docstring_pattern = r'"""(.*?)"""'
        docstring_match = re.search(docstring_pattern, class_body[match.end():match.end() + 500], re.DOTALL)
        if docstring_match:
            docstring = docstring_match.group(1).strip()
        
        # Fallback to looking for a comment
        if not docstring:
            # Look for a comment on the same line or the line above
            line_start = class_body.rfind('\n', 0, match.start()) + 1
            line_end = class_body.find('\n', match.start())
            line = class_body[line_start:line_end]
            
            comment_match = re.search(r'#\s*(.*)', line)
            if comment_match:
                docstring = comment_match.group(1).strip()
            else:
                # Check if there's a comment in the previous line
                prev_line_end = line_start - 1
                prev_line_start = class_body.rfind('\n', 0, prev_line_end) + 1
                prev_line = class_body[prev_line_start:prev_line_end]
                
                prev_comment_match = re.search(r'#\s*(.*)', prev_line)
                if prev_comment_match:
                    docstring = prev_comment_match.group(1).strip()
        
        # Create simplified property data
        property_data = {
            "name": name,
            "type": type_annotation,
            "description": docstring
        }
        
        # Try to extract enum values from type or description
        enum_type = None
        
        # Check if the type or a part of it matches a known enum type
        for enum_type_name, enum_info in TYPE_MAPPINGS.items():
            if enum_type_name in type_annotation:
                enum_type = enum_type_name
                # Add the enum values from our mapping
                property_data["values"] = enum_info["values"]
                break
        
        # If we didn't find a match in known types, try to extract from description
        if "values" not in property_data:
            enum_values = extract_enum_values_from_description(docstring)
            if enum_values:
                property_data["values"] = enum_values
        
        # Add to the appropriate list, but for events just track the name
        if is_event:
            if "event_names" not in spec:
                spec["event_names"] = []
            if name not in spec["event_names"]:
                spec["event_names"].append(name)
        elif name in ["size", "variant", "color_scheme", "radius"] or name.endswith("_style"):
            spec["styling_props"].append(property_data)
        else:
            spec["properties"].append(property_data)
    
    # Then get class attributes with assignments but no type annotations
    assign_pattern = re.compile(r'(?:^|\n)\s*([\w]+)\s*=\s*([^:\n]+)(?:$|\n)', re.MULTILINE)
    for match in re.finditer(assign_pattern, class_body):
        name = match.group(1)
        if should_skip_property(name):
            continue
        
        # Skip if already processed with type annotation
        if any(p.get("name") == name for p in spec["properties"] + spec["styling_props"]):
            continue
            
        # Skip if property is in a method section
        if any(start <= match.start() <= end for start, end in method_sections):
            continue
        
        # Check if this is a property or an event handler
        is_event = name.startswith('on_')
        
        # Try to infer the type from the assignment
        value = match.group(2).strip()
        inferred_type = "Any"
        
        if value == "True" or value == "False":
            inferred_type = "bool"
        elif value.startswith('"') or value.startswith("'"):
            inferred_type = "str"
        elif value.isdigit():
            inferred_type = "int"
        elif "." in value and all(part.isdigit() for part in value.split(".")):
            inferred_type = "float"
        
        # Extract docstring or comment (same as above)
        docstring = ''
        
        # Look for a docstring in triple quotes after the property
        docstring_pattern = r'"""(.*?)"""'
        docstring_match = re.search(docstring_pattern, class_body[match.end():match.end() + 500], re.DOTALL)
        if docstring_match:
            docstring = docstring_match.group(1).strip()
        
        # Fallback to looking for a comment
        if not docstring:
            # Look for a comment on the same line or the line above
            line_start = class_body.rfind('\n', 0, match.start()) + 1
            line_end = class_body.find('\n', match.start())
            line = class_body[line_start:line_end]
            
            comment_match = re.search(r'#\s*(.*)', line)
            if comment_match:
                docstring = comment_match.group(1).strip()
            else:
                # Check if there's a comment in the previous line
                prev_line_end = line_start - 1
                prev_line_start = class_body.rfind('\n', 0, prev_line_end) + 1
                prev_line = class_body[prev_line_start:prev_line_end]
                
                prev_comment_match = re.search(r'#\s*(.*)', prev_line)
                if prev_comment_match:
                    docstring = prev_comment_match.group(1).strip()
        
        # Create simplified property data
        property_data = {
            "name": name,
            "type": inferred_type,
            "description": docstring
        }
        
        # Try to extract enum values from description
        enum_values = extract_enum_values_from_description(docstring)
        if enum_values:
            property_data["values"] = enum_values
        
        # Add to the appropriate list, but for events just track the name
        if is_event:
            if "event_names" not in spec:
                spec["event_names"] = []
            if name not in spec["event_names"]:
                spec["event_names"].append(name)
        elif name in ["size", "variant", "color_scheme", "radius"] or name.endswith("_style"):
            spec["styling_props"].append(property_data)
        else:
            spec["properties"].append(property_data)

def find_all_components(base_dir):
    """Find all components in the codebase.
    
    Returns a dictionary of component names to their module paths and file paths.
    This function focuses on components specifically requested by the user.
    """
    # Component mappings from __init__.pyi file
    component_mappings = extract_component_mappings(base_dir)
    
    # Add specialized mappings for common components that have special file paths
    specialized_mappings = {
        # Components that live in nested directories
        "audio": {
            "module_path": "components.react_player.react_player",
            "file_path": f"{base_dir}/reflex/reflex/components/react_player/react_player.py"
        },
        "video": {
            "module_path": "components.react_player.react_player",
            "file_path": f"{base_dir}/reflex/reflex/components/react_player/react_player.py"
        },
        "icon": {
            "module_path": "components.lucide.icon",
            "file_path": f"{base_dir}/reflex/reflex/components/lucide/icon.py"
        },
        "moment": {
            "module_path": "components.moment.moment",
            "file_path": f"{base_dir}/reflex/reflex/components/moment/moment.py"
        },
        "markdown": {
            "module_path": "components.markdown.markdown",
            "file_path": f"{base_dir}/reflex/reflex/components/markdown/markdown.py"
        },
        "editor": {
            "module_path": "components.suneditor.suneditor",
            "file_path": f"{base_dir}/reflex/reflex/components/suneditor/suneditor.py"
        },
        "data_table": {
            "module_path": "components.gridjs.gridjs",
            "file_path": f"{base_dir}/reflex/reflex/components/gridjs/gridjs.py"
        },
        # Special components that need specific handling
        "areachart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "barchart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "composedchart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py" 
        },
        "funnelchart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "linechart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "piechart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "radarchart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "radialbarchart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "scatterchart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "ag_grid": {
            "module_path": "components.datadisplay.ag_grid",
            "file_path": f"{base_dir}/reflex/reflex/components/datadisplay/ag_grid.py"
        },
        "code_block": {
            "module_path": "components.datadisplay.code",
            "file_path": f"{base_dir}/reflex/reflex/components/datadisplay/code.py"
        },
        "data_editor": {
            "module_path": "components.datadisplay.dataeditor",
            "file_path": f"{base_dir}/reflex/reflex/components/datadisplay/dataeditor.py"
        },
        "el": {
            "module_path": "components.el",
            "file_path": f"{base_dir}/reflex/reflex/components/el/__init__.py"
        },
        "list": {
            "module_path": "components.el.elements.list",
            "file_path": f"{base_dir}/reflex/reflex/components/el/elements/list.py"
        },
        
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
        },
        
        # Core components
        "clipboard": {
            "module_path": "components.core.clipboard",
            "file_path": f"{base_dir}/reflex/reflex/components/core/clipboard.py"
        },
        "cond": {
            "module_path": "components.core.cond",
            "file_path": f"{base_dir}/reflex/reflex/components/core/cond.py"
        },
        "foreach": {
            "module_path": "components.core.foreach",
            "file_path": f"{base_dir}/reflex/reflex/components/core/foreach.py"
        },
        "match": {
            "module_path": "components.core.match",
            "file_path": f"{base_dir}/reflex/reflex/components/core/match.py"
        },
        "upload": {
            "module_path": "components.core.upload",
            "file_path": f"{base_dir}/reflex/reflex/components/core/upload.py"
        },
        
        # Base components
        "fragment": {
            "module_path": "components.base.fragment",
            "file_path": f"{base_dir}/reflex/reflex/components/base/fragment.py"
        },
        "script": {
            "module_path": "components.base.script",
            "file_path": f"{base_dir}/reflex/reflex/components/base/script.py"
        },
        
        # HTML elements
        "image": {
            "module_path": "components.el.elements.media",
            "file_path": f"{base_dir}/reflex/reflex/components/el/elements/media.py"
        },
        
        # Sonner components
        "toast": {
            "module_path": "components.sonner.toast",
            "file_path": f"{base_dir}/reflex/reflex/components/sonner/toast.py"
        },
        
        # Recharts components
        "axis": {
            "module_path": "components.recharts.cartesian",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/cartesian.py"
        },
        "brush": {
            "module_path": "components.recharts.cartesian",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/cartesian.py"
        },
        "cartesiangrid": {
            "module_path": "components.recharts.cartesian",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/cartesian.py"
        },
        "errorbar": {
            "module_path": "components.recharts.cartesian",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/cartesian.py"
        },
        "reference": {
            "module_path": "components.recharts.cartesian",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/cartesian.py"
        },
        "legend": {
            "module_path": "components.recharts.general",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/general.py"
        },
        "recharts": {
            "module_path": "components.recharts.general",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/general.py"
        }
    }
    
    # Add specialized mappings to component_mappings
    for component_name, mapping in specialized_mappings.items():
        component_mappings[component_name] = mapping
    
    # These are the components explicitly requested by the user
    requested_components = [
        # Common UI components
        "accordion", "alert_dialog", "avatar", "badge", "blockquote", "box", "button",
        "callout", "card", "center", "checkbox", "clipboard", "code", "code_block",
        "container", "context_menu", "data_editor", "data_list", "data_table", "dialog",
        "drawer", "dropdown_menu", "flex", "form", "fragment", "grid", "heading", "hover_card",
        "hstack", "html_embed", "icon", "image", "input", "inset", "link", "list", "markdown",
        "popover", "progress", "radio_group", "scroll_area", "section", "segmented_control",
        "select", "separator", "skeleton", "slider", "spacer", "spinner", "stack", "switch",
        "table", "tabs", "text", "text_area", "theme", "toast", "tooltip", "upload", "vstack",
        
        # Cond and foreach components
        "cond", "foreach", "match",
        
        # Media components
        "audio", "editor", "video",
        
        # Time components
        "moment",
        
        # Script component
        "script",
        
        # Graphing components
        "ag_grid", "areachart", "axis", "barchart", "brush", "cartesiangrid",
        "composedchart", "errorbar", "funnelchart", "legend", "linechart", "piechart",
        "radarchart", "radialbarchart", "recharts", "reference", "scatterchart"
    ]
    
    # Final mapping of all components
    all_components = {}
    
    # Handle components from component_mappings
    for component_name in requested_components:
        if component_name in component_mappings:
            all_components[component_name] = component_mappings[component_name]
        else:
            # Try to find a path for the component
            print(f"  Warning: Could not resolve path for component {component_name}")
    
    return all_components

def generate_spec_files():
    """Generate spec files for all components."""
    base_dir = os.getcwd()
    print("Griffe version: unknown")
    
    # Generate common props spec
    common_props_spec = generate_common_props_spec()
    common_props_spec_file = os.path.join("specs", "common_props.json")
    os.makedirs(os.path.dirname(common_props_spec_file), exist_ok=True)
    with open(common_props_spec_file, "w") as f:
        json.dump(common_props_spec, f, indent=2)
    print(f"Common props spec file saved to: {os.path.abspath(common_props_spec_file)}")
    
    # Find all components in the codebase
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
            spec = {
                "name": component_name,
                "module_path": mapping['module_path'],
                "file_path": mapping['file_path'],
                "docstring": "",
                "bases": [],
                "properties": [],
                "event_names": [],
                "enum_values": {},
                "styling_properties": {},
                "subcomponents": {}
            }
            
            # Save spec to file
            spec_path = os.path.join(SPECS_DIR, f"{component_name}.json")
            os.makedirs(os.path.dirname(spec_path), exist_ok=True)
            with open(spec_path, "w") as f:
                json.dump(spec, f, indent=2)
            
            print(f"  Spec file saved to: {spec_path}")
            failure_count += 1
            continue
        
        # Extract component information
        try:
            spec = extract_component_info(component_name, mapping, None)
            
            # Save spec to file
            spec_path = os.path.join(SPECS_DIR, f"{component_name}.json")
            os.makedirs(os.path.dirname(spec_path), exist_ok=True)
            with open(spec_path, "w") as f:
                json.dump(spec, f, indent=2)
            
            print(f"  Spec file saved to: {spec_path}")
            success_count += 1
            
            if "error" in spec:
                failure_count += 1
        except Exception as e:
            print(f"  Error extracting component info: {str(e)}")
            failure_count += 1
    
    print(f"\nProcessed {processed} components with {failure_count} failures")
    print(f"Spec files saved to: {SPECS_DIR}")

def generate_common_props_spec():
    """Generate a compact spec file for common properties"""
    common_props_spec = {
        "name": "common_props",
        "description": "Common properties shared by most Reflex components",
        "events": COMMON_EVENT_HANDLERS,  # Just a list of event names
        "categories": {}
    }
    
    # Add common prop categories
    for category, props in COMMON_PROP_CATEGORIES.items():
        category_name = f"{category}_props"
        common_props_spec["categories"][category_name] = {
            "description": f"Common {category} props",
            "props": props  # Just the list of property names
        }
    
    # Add type mappings with enum values
    common_props_spec["type_mappings"] = TYPE_MAPPINGS
    
    # Save the common props spec
    common_props_spec_path = SPECS_DIR / "common_props.json"
    with open(common_props_spec_path, 'w') as f:
        json.dump(common_props_spec, f, indent=2)
    
    print(f"Common props spec file saved to: {common_props_spec_path}")

if __name__ == "__main__":
    generate_spec_files() 