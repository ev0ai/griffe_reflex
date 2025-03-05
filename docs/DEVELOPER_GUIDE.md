# Reflex Component Specification Generator: Developer Guide

This guide provides information for developers who want to extend or modify the Reflex Component Specification Generator. It covers common extension scenarios and best practices.

## Table of Contents

1. [Adding New Component Mappings](#adding-new-component-mappings)
2. [Handling Custom Property Types](#handling-custom-property-types)
3. [Enhancing Enum Value Extraction](#enhancing-enum-value-extraction)
4. [Modifying Output Format](#modifying-output-format)
5. [Adding New Extraction Logic](#adding-new-extraction-logic)
6. [Best Practices](#best-practices)

## Adding New Component Mappings

The most common extension is adding mappings for new component types. This involves creating or updating a mapping module.

### Example: Adding a New Component Category

Let's say you want to add mappings for a new category of components called "custom_widgets".

1. **Create or update a mapping module**:

```python
# spec_generator/mapping/custom_widgets.py
from typing import Dict, Any

def get_custom_widget_mappings(base_dir: str) -> Dict[str, Dict[str, str]]:
    """Get mappings for custom widget components.
    
    Args:
        base_dir: Base directory of the Reflex codebase
        
    Returns:
        A dictionary of component names to their module paths and file paths.
    """
    return {
        "my_widget": {
            "module_path": "components.custom_widgets.my_widget",
            "file_path": f"{base_dir}/reflex/reflex/components/custom_widgets/my_widget.py"
        },
        "fancy_button": {
            "module_path": "components.custom_widgets.fancy_button",
            "file_path": f"{base_dir}/reflex/reflex/components/custom_widgets/fancy_button.py"
        }
    }
```

2. **Update the mapping `__init__.py` file**:

```python
# spec_generator/mapping/__init__.py
from spec_generator.mapping.base import extract_component_mappings, get_base_mappings
from spec_generator.mapping.specialized import get_specialized_mappings
from spec_generator.mapping.ag_grid import get_ag_grid_mappings
from spec_generator.mapping.radix import get_radix_mappings
from spec_generator.mapping.core import get_core_mappings
# Add your new mapping import:
from spec_generator.mapping.custom_widgets import get_custom_widget_mappings

__all__ = [
    "extract_component_mappings",
    "get_base_mappings",
    "get_specialized_mappings",
    "get_ag_grid_mappings",
    "get_radix_mappings",
    "get_core_mappings",
    # Add your new mapping function:
    "get_custom_widget_mappings"
]
```

3. **Update the discovery module**:

```python
# spec_generator/discovery.py
from spec_generator.mapping import (
    get_base_mappings,
    get_specialized_mappings,
    get_ag_grid_mappings,
    get_radix_mappings,
    get_core_mappings,
    # Add your new mapping import:
    get_custom_widget_mappings
)

def find_all_components(base_dir: str) -> Dict[str, Dict[str, str]]:
    """Find all components in the codebase."""
    # Get the base component mappings
    components = get_base_mappings(base_dir)
    
    # Add specialized mappings
    components.update(get_specialized_mappings(base_dir))
    
    # Add AG Grid mappings
    components.update(get_ag_grid_mappings(base_dir))
    
    # Add Radix mappings
    components.update(get_radix_mappings(base_dir))
    
    # Add Core and other mappings
    components.update(get_core_mappings(base_dir))
    
    # Add your new custom widget mappings:
    components.update(get_custom_widget_mappings(base_dir))
    
    # Filter out invalid components
    invalid_components = ["component", "next_link", "nextlink", "nossrcomponent"]
    for invalid_comp in invalid_components:
        if invalid_comp in components:
            del components[invalid_comp]
    
    # Filter out components with spaces in their names
    components = {k: v for k, v in components.items() if ' as ' not in k}
    
    print(f"Found {len(components)} components")
    
    return components
```

## Handling Custom Property Types

If you need to handle custom property types or enums, you can update the property extraction logic.

### Example: Adding a New Enum Type Mapping

1. **Update the property extraction module**:

```python
# In spec_generator/extraction/properties.py

# Add your custom enum type to the TYPE_MAPPINGS dictionary:
TYPE_MAPPINGS = {
    "LiteralVariant": {
        "values": ["solid", "soft", "outline", "ghost"]
    },
    "LiteralButtonSize": {
        "values": ["1", "2", "3", "4"]
    },
    # Add your new enum type:
    "CustomWidgetSize": {
        "values": ["small", "medium", "large", "xlarge"]
    }
}
```

## Enhancing Enum Value Extraction

You can enhance the enum value extraction logic to handle additional patterns in property descriptions.

### Example: Adding Support for New Enum Format

1. **Update the enum parser**:

```python
# spec_generator/utils/enum_parser.py
def extract_enum_values_from_description(description: str) -> Optional[List[str]]:
    """Extract enum values from description strings."""
    # Check for numeric range pattern like "1" - "9"
    range_match = re.search(r'"(\d+)"\s*-\s*"(\d+)"', description)
    if range_match:
        start = int(range_match.group(1))
        end = int(range_match.group(2))
        return [str(i) for i in range(start, end + 1)]
    
    # Find patterns like "value1" | "value2" | "value3"
    enum_match = re.search(r'(?:"([^"]+)"(?:\s*\|\s*"([^"]+)")+)', description)
    if enum_match:
        # Extract all double-quoted values
        values = re.findall(r'"([^"]+)"', description)
        return values
        
    # Add your custom pattern, e.g., for comma-separated values:
    comma_match = re.search(r'Options:\s*"([^"]+)"(?:\s*,\s*"([^"]+)")+', description)
    if comma_match:
        values = re.findall(r'"([^"]+)"', description)
        return values
        
    return None
```

## Modifying Output Format

You can modify the output format by updating the output module.

### Example: Adding Additional Fields to the Specification

1. **Update the output writer**:

```python
# spec_generator/output/writer.py
def create_empty_spec(component_name: str, mapping: Dict[str, str]) -> Dict[str, Any]:
    """Create an empty spec for a component."""
    spec = {
        "name": component_name,
        "module_path": mapping.get("module_path", ""),
        "module_name": mapping.get("module_path", "").split(".")[-1],
        "file_path": mapping.get("file_path", ""),
        "doc_path": None,
        "docstring": "",
        "bases": [],
        "supports_common_props": True,
        "properties": [],
        "event_names": [],
        "styling_props": [],
        "subcomponents": {},
        # Add your custom fields:
        "category": get_component_category(component_name),
        "examples": [],
        "version_added": "1.0.0"
    }
    return spec

def get_component_category(component_name: str) -> str:
    """Determine the category of a component based on its name."""
    categories = {
        "button": "input",
        "text": "typography",
        "flex": "layout",
        # Add more categorizations
    }
    return categories.get(component_name, "other")
```

## Adding New Extraction Logic

You can add new extraction logic to analyze additional aspects of components.

### Example: Extracting Usage Examples

1. **Create a new extraction module**:

```python
# spec_generator/extraction/examples.py
import re
from typing import List, Dict, Any

def extract_examples_from_docstring(docstring: str) -> List[Dict[str, str]]:
    """Extract code examples from component docstrings.
    
    Args:
        docstring: The component docstring
        
    Returns:
        A list of examples with description and code
    """
    examples = []
    
    # Look for Examples section in docstring
    example_section = re.search(r'Examples\s*:?\s*\n([\s\S]+?)(?:\n\n|$)', docstring)
    if not example_section:
        return examples
        
    # Extract individual examples
    example_blocks = re.findall(r'```(?:python|jsx)?\s*\n([\s\S]+?)```', example_section.group(1))
    
    for i, code in enumerate(example_blocks):
        # Try to find a description before the code block
        desc_match = re.search(r'(\S[^\n]+)\s*\n\s*```', example_section.group(1))
        description = desc_match.group(1) if desc_match else f"Example {i+1}"
        
        examples.append({
            "description": description,
            "code": code.strip()
        })
        
    return examples
```

2. **Update the component extraction to use your new function**:

```python
# spec_generator/extraction/component.py
from spec_generator.extraction.examples import extract_examples_from_docstring

def extract_component_info(component_name: str, component_data: Dict[str, str], doc_path: Optional[Path] = None) -> Dict[str, Any]:
    # ... existing extraction code ...
    
    # Extract docstring
    if docstring_match:
        docstring = clean_docstring(docstring_match.group(1))
        spec["docstring"] = docstring
        
        # Extract examples using your new function
        examples = extract_examples_from_docstring(docstring)
        if examples:
            spec["examples"] = examples
    
    # ... rest of the extraction code ...
```

## Best Practices

When extending the specification generator, follow these best practices:

1. **Maintain Modularity**: Keep related functionality in appropriate modules.
2. **Write Tests**: Add tests for your new functionality to ensure it works as expected.
3. **Handle Edge Cases**: Be robust against missing or malformed input.
4. **Document Changes**: Update documentation to reflect your changes.
5. **Follow Patterns**: Use the same patterns and conventions as the existing code.
6. **Backward Compatibility**: Ensure your changes don't break existing functionality.

### Component Mapping Guidelines

- Each component mapping should include both `module_path` and `file_path`
- Be consistent with naming conventions
- Group related components in the same mapping module
- Filter out test or internal components

### Property Extraction Guidelines

- Be careful with regular expressions for extracting properties
- Clean property descriptions for readability
- Normalize property names for consistency
- Extract enum values whenever possible
- Categorize properties appropriately (regular, styling, events)

### Output Format Guidelines

- Keep the output JSON format consistent and clean
- Use descriptive property and field names
- Follow JSON schema best practices
- Include all necessary information for consumers of the specifications

By following these guidelines and examples, you can extend the Reflex Component Specification Generator to meet your specific needs while maintaining compatibility with the existing system. 