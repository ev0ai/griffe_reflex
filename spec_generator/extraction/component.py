import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

from spec_generator.extraction.properties import extract_properties_from_class_body
from spec_generator.utils import print_debug

# Common Reflex event handlers that should be included in all component specs
COMMON_EVENT_HANDLERS: List[str] = [
    "on_blur", "on_click", "on_context_menu", "on_double_click", "on_focus",
    "on_mount", "on_mouse_down", "on_mouse_enter", "on_mouse_leave", "on_mouse_move",
    "on_mouse_out", "on_mouse_over", "on_mouse_up", "on_scroll", "on_unmount"
]


def extract_component_info(component_name: str, component_data: Dict[str, str], doc_path: Optional[Path] = None) -> Dict[str, Any]:
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
            class_body = extract_class_body(content, class_start)
            
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
            spec["supports_common_props"] = check_supports_common_props(spec["bases"])
            
            # Add standard event handlers if component supports common props - just the names
            if spec["supports_common_props"] and not spec.get('error'):
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
                            sc_body = extract_class_body(content, sc_start)
                            
                            # Extract subcomponent base classes to check if it supports common props
                            sc_bases_match = re.search(rf"class\s+{sc_class}\s*\((.*?)\)\s*:", sc_body)
                            sc_bases = []
                            
                            if sc_bases_match:
                                sc_bases = [base.strip() for base in sc_bases_match.group(1).split(',')]
                            
                            # Check if supports common props
                            sc_supports_common_props = check_supports_common_props(sc_bases)
                            
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
                                "supports_common_props": sc_supports_common_props,
                                "properties": [],
                                "event_names": [],
                                "styling_props": []
                            }
                            
                            # Add common event handlers if this component supports common props
                            if sc_supports_common_props:
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


def extract_class_body(content: str, class_start: int) -> str:
    """Extract the class body from the file content.
    
    Args:
        content: The file content.
        class_start: The start position of the class.
        
    Returns:
        The class body.
    """
    class_body = ""
    open_braces = 0
    in_class = True
    
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
    
    return class_body


def check_supports_common_props(bases: List[str]) -> bool:
    """Check if a component supports common properties based on its base classes.
    
    Args:
        bases: List of base class names.
        
    Returns:
        True if the component supports common properties, False otherwise.
    """
    common_base_indicators = ["Component", "Element", "RadixThemesComponent", "HTMLElement", "Box", "Div", "Link"]
    
    for base in bases:
        if any(common_base in base for common_base in common_base_indicators):
            return True
    
    return False 