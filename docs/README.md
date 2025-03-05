# Reflex Component Specification Generator Documentation

Welcome to the documentation for the Reflex Component Specification Generator.

## Table of Contents

1. [Architecture](ARCHITECTURE.md) - Overview of the system architecture
2. [Developer Guide](DEVELOPER_GUIDE.md) - Guide for extending the system

## Overview

The Reflex Component Specification Generator is a tool for extracting component specifications from the Reflex codebase. It produces JSON specification files that can be used for documentation, code generation, and IDE integrations.

Key features:

- Generates comprehensive specifications for 86+ Reflex components
- Extracts component properties, events, and styling information
- Handles component inheritance and subcomponents
- Identifies enum values from property descriptions
- Generates a common props specification for shared properties

## Getting Started

To learn more about how the system works, start with the [Architecture](ARCHITECTURE.md) document, which provides an overview of the system components and their relationships.

For developers who want to extend or modify the system, the [Developer Guide](DEVELOPER_GUIDE.md) provides detailed instructions and examples.

## Specification Format

The generated specifications follow a consistent JSON format:

```json
{
  "name": "component_name",
  "module_path": "components.path.to.component",
  "module_name": "component",
  "file_path": "/path/to/component.py",
  "docstring": "Component description",
  "bases": ["BaseClass1", "BaseClass2"],
  "supports_common_props": true,
  "properties": [
    {
      "name": "property_name",
      "type": "PropertyType",
      "description": "Property description"
    }
  ],
  "event_names": ["on_click", "on_hover"],
  "styling_props": [
    {
      "name": "size",
      "type": "SizeType",
      "description": "Size description",
      "values": ["1", "2", "3"]
    }
  ],
  "subcomponents": {}
}
```

For more details on the specification format, see the `create_empty_spec` function in `spec_generator/output/writer.py`. 