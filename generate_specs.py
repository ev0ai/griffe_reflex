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

def print_debug(*args, **kwargs):
    """Debug print function."""
    # Uncomment to enable debug printing
    # print(*args, **kwargs)
    pass

def extract_component_mappings():
    """
    Extract component mappings from the __init__.py and __init__.pyi files.
    
    Returns a dictionary of component names to their module paths and file paths.
    """
    # Use the pyi file to get accurate import mappings
    with open(pyi_path, 'r') as f:
        pyi_content = f.read()
    
    # Find all component imports
    component_to_module = {}
    import_pattern = r'from\s+(\.components\.[^\s]+)\s+import\s+([^\s]+)\s+as\s+([^\s]+)'
    
    for match in re.finditer(import_pattern, pyi_content):
        module_path = match.group(1).replace('.', '', 1)  # Remove leading dot
        module_name = match.group(2)
        component_name = match.group(3)
        
        component_to_module[component_name] = (module_path, module_name)
    
    # Convert module paths to file paths
    component_to_paths = {}
    for component_name, (module_path, module_name) in component_to_module.items():
        # Convert module path to file path
        file_path = module_path.replace('.', '/') + '.py'
        # Use the correct path starting with reflex/reflex/
        file_path = str(REFLEX_ROOT / 'reflex' / file_path)
        
        component_to_paths[component_name] = {
            'module_path': module_path,
            'module_name': module_name,
            'file_path': file_path
        }
    
    return component_to_paths

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
    Extract component information from the source code.
    
    Args:
        component_name: The name of the component.
        component_data: Dictionary with module_path, module_name, and file_path.
        doc_path: Path to the documentation file.
        
    Returns:
        A dictionary containing component information.
    """
    module_path = component_data['module_path']
    module_name = component_data['module_name']
    file_path = component_data['file_path']
    
    # Basic component structure to fill
    spec = {
        "name": component_name,
        "module_path": module_path,
        "module_name": module_name,
        "file_path": file_path,
        "doc_path": str(doc_path),
        "docstring": "",
        "bases": [],
        "properties": [],
        "events": [],
        "styling_props": []
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
                            
                            # Extract properties from subcomponent
                            extract_properties_from_class_body(sc_body, spec, sc_class)
            
            # Extract properties
            extract_properties_from_class_body(class_body, spec)
        
        else:
            print(f"  Warning: No suitable class found in {file_path}")
            spec["error"] = f"No suitable class found"
    
    except Exception as e:
        print(f"  Error extracting info from file {file_path}: {e}")
        spec["error"] = f"Failed to extract component info: {str(e)}"
    
    return spec

def extract_properties_from_class_body(class_body, spec, class_prefix=None):
    """
    Extract properties from a class body and add them to the spec.
    
    Args:
        class_body: The class body text
        spec: The spec dictionary to update
        class_prefix: Optional prefix to add to property names to indicate the source class
    """
    # Extract properties
    property_pattern = r"^\s+(\w+)\s*:\s*(?:Var\[)?([^=\n]+?)(?:\])?\s*(?:=|$)"
    for prop_match in re.finditer(property_pattern, class_body, re.MULTILINE):
        prop_name = prop_match.group(1)
        prop_type = prop_match.group(2).strip()
        
        # Skip special methods
        if prop_name.startswith('__') and prop_name.endswith('__'):
            continue
        
        # Extract property docstring
        prop_docstring = ""
        prop_context = class_body[max(0, prop_match.start() - 100):min(len(class_body), prop_match.end() + 100)]
        prop_docstring_match = re.search(rf"{prop_name}\s*:.*?\n\s+\"\"\"(.*?)\"\"\"", prop_context, re.DOTALL)
        
        # If no docstring found in the property definition, look for comment directly above
        if not prop_docstring_match:
            line_start = prop_match.start()
            while line_start > 0 and class_body[line_start] != '\n':
                line_start -= 1
            
            # Look for a comment line above
            comment_start = class_body.rfind('\n', 0, line_start) + 1
            comment_line = class_body[comment_start:line_start].strip()
            if comment_line.startswith('#'):
                prop_docstring = comment_line[1:].strip()
        
        if prop_docstring_match:
            prop_docstring = prop_docstring_match.group(1).strip()
        
        # Prefix the property name if specified
        display_name = prop_name
        if class_prefix:
            display_name = f"{class_prefix}.{prop_name}"
        
        prop_info = {
            "name": display_name,
            "type": prop_type,
            "docstring": prop_docstring
        }
        
        # Categorize properties
        if prop_name.startswith("on_"):
            spec["events"].append(prop_info)
        elif prop_name in ["style", "class_name", "color_scheme", "variant", "size", "width", "height", "radius"]:
            spec["styling_props"].append(prop_info)
        else:
            spec["properties"].append(prop_info)

def generate_spec_files():
    """
    Generate spec files for all documented components.
    """
    # Extract component mappings
    component_mappings = extract_component_mappings()
    
    # Scan library docs
    component_to_doc_path = scan_library_docs()
    
    # Track processed components and failures
    processed = 0
    failures = 0
    
    # Process each component
    for component_name, doc_path in component_to_doc_path.items():
        print(f"Processing component: {component_name}")
        
        # Resolve the component path
        if component_name in component_mappings:
            component_data = component_mappings[component_name]
            print(f"  Module path: {component_data['module_path']}")
            print(f"  File path: {component_data['file_path']}")
            
            # Extract component information
            spec = extract_component_info(component_name, component_data, doc_path)
            
            # Save spec to file
            spec_path = SPECS_DIR / f"{component_name}.json"
            with open(spec_path, 'w') as f:
                json.dump(spec, f, indent=2)
            
            print(f"  Spec file saved to: {spec_path}")
            processed += 1
            
            if "error" in spec:
                failures += 1
        else:
            print(f"  Warning: Could not resolve path for component {component_name}")
            failures += 1
    
    print(f"\nProcessed {processed} components with {failures} failures")
    print(f"Spec files saved to: {SPECS_DIR}")

if __name__ == "__main__":
    generate_spec_files() 