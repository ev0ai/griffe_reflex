import re
from typing import Dict, Any, List

from spec_generator.utils import extract_enum_values_from_description

# Enum type mappings for standardized property values
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


def should_skip_property(name: str) -> bool:
    """Check if a property should be skipped from extraction.
    
    Args:
        name: The property name to check
        
    Returns:
        True if the property should be skipped, False otherwise
    """
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


def extract_properties_from_class_body(class_body: str, spec: Dict[str, Any], class_prefix: str = None) -> None:
    """Extract properties from a class body.
    
    Args:
        class_body: The class body text to extract properties from
        spec: The specification dictionary to update with extracted properties
        class_prefix: Optional prefix for class names
    """
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
        docstring = extract_docstring_or_comment(class_body, match.end())
        
        # Create simplified property data
        property_data = {
            "name": name,
            "type": type_annotation,
            "description": docstring
        }
        
        # Fix property name for "as_" to "_as"
        if name == "as_":
            property_data["name"] = "_as"
        
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
                
                # Clean up the description to remove the enum format text
                # Remove patterns like: "value1" | "value2" | "value3"
                cleaned_desc = re.sub(r'(?::\s*)?"[^"]+"\s*(?:\|\s*"[^"]+")+', '', docstring).strip()
                # Remove patterns like: "1" - "9"
                cleaned_desc = re.sub(r'(?::\s*)?"[^"]+"\s*-\s*"[^"]+"', '', cleaned_desc).strip()
                
                # If we end up with trailing colon, remove it
                if cleaned_desc.endswith(':'):
                    cleaned_desc = cleaned_desc[:-1].strip()
                
                # Remove trailing pipe characters that might be left
                cleaned_desc = re.sub(r'\|\s*$', '', cleaned_desc).strip()
                
                property_data["description"] = cleaned_desc
        
        # Add to the appropriate list, but for events just track the name
        if is_event:
            if "event_names" not in spec:
                spec["event_names"] = []
            if name not in spec["event_names"]:
                spec["event_names"].append(name)
        elif name in ["size", "variant", "color_scheme", "radius"] or name.endswith("_style"):
            if "styling_props" not in spec:
                spec["styling_props"] = []
            spec["styling_props"].append(property_data)
        else:
            if "properties" not in spec:
                spec["properties"] = []
            spec["properties"].append(property_data)
    
    # Then get class attributes with assignments but no type annotations
    assign_pattern = re.compile(r'(?:^|\n)\s*([\w]+)\s*=\s*([^:\n]+)(?:$|\n)', re.MULTILINE)
    for match in re.finditer(assign_pattern, class_body):
        name = match.group(1)
        if should_skip_property(name):
            continue
        
        # Skip if already processed with type annotation
        if "properties" in spec and any(p.get("name") == name for p in spec["properties"]):
            continue
        if "styling_props" in spec and any(p.get("name") == name for p in spec["styling_props"]):
            continue
            
        # Skip if property is in a method section
        if any(start <= match.start() <= end for start, end in method_sections):
            continue
        
        # Check if this is a property or an event handler
        is_event = name.startswith('on_')
        
        # Try to infer the type from the assignment
        value = match.group(2).strip()
        inferred_type = infer_type_from_value(value)
        
        # Extract docstring or comment
        docstring = extract_docstring_or_comment(class_body, match.end())
        
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
            if "styling_props" not in spec:
                spec["styling_props"] = []
            spec["styling_props"].append(property_data)
        else:
            if "properties" not in spec:
                spec["properties"] = []
            spec["properties"].append(property_data)


def extract_docstring_or_comment(class_body: str, match_end: int) -> str:
    """Extract docstring or comment for a property.
    
    Args:
        class_body: The class body text
        match_end: The end position of the property match
        
    Returns:
        The extracted docstring or comment
    """
    docstring = ''
    
    # Look for a docstring in triple quotes after the property
    docstring_pattern = r'"""(.*?)"""'
    docstring_match = re.search(docstring_pattern, class_body[match_end:match_end + 500], re.DOTALL)
    if docstring_match:
        docstring = docstring_match.group(1).strip()
        return docstring
    
    # Look for a comment on the same line or the line above
    line_start = class_body.rfind('\n', 0, match_end) + 1
    line_end = class_body.find('\n', match_end)
    line = class_body[line_start:line_end]
    
    comment_match = re.search(r'#\s*(.*)', line)
    if comment_match:
        docstring = comment_match.group(1).strip()
        return docstring
    
    # Check if there's a comment in the previous line
    prev_line_end = line_start - 1
    prev_line_start = class_body.rfind('\n', 0, prev_line_end) + 1
    prev_line = class_body[prev_line_start:prev_line_end]
    
    prev_comment_match = re.search(r'#\s*(.*)', prev_line)
    if prev_comment_match:
        docstring = prev_comment_match.group(1).strip()
        
    return docstring


def infer_type_from_value(value: str) -> str:
    """Infer the type of a property from its assigned value.
    
    Args:
        value: The assigned value as a string
        
    Returns:
        The inferred type as a string
    """
    inferred_type = "Any"
    
    if value == "True" or value == "False":
        inferred_type = "bool"
    elif value.startswith('"') or value.startswith("'"):
        inferred_type = "str"
    elif value.isdigit():
        inferred_type = "int"
    elif "." in value and all(part.isdigit() for part in value.split(".")):
        inferred_type = "float"
        
    return inferred_type 