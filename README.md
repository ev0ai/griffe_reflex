# Reflex Component Specification Generator

This tool extracts component specifications from the Reflex codebase and generates JSON files that can be used for documentation, code generation, and IDE integrations.

## Features

- **Comprehensive**: Generates specs for 86+ Reflex components
- **Modular**: Well-organized codebase with dedicated modules for mapping, extraction, and output
- **Enum Support**: Properly extracts enum values from property descriptions
- **Clean Output**: Generates clean, well-formatted JSON specs
- **Error Handling**: Gracefully handles components with missing files

## Documentation

For detailed documentation about the architecture and how to extend the system, see the [documentation directory](docs/).

## Usage

There are several ways to use the specification generator:

### Direct Script Execution

You can run the provided script directly:

```bash
./generate_specs_reflex.py
```

You can also use command line arguments:

```bash
# Only generate common props spec
./generate_specs_reflex.py --only-common-props

# Clean specs directory before generating
./generate_specs_reflex.py --clean

# Specify base directory and output directory
./generate_specs_reflex.py --base-dir /path/to/reflex --specs-dir /path/to/output
```

### Programmatic Usage

You can also import and use the functions directly in Python:

```python
from spec_generator import generate_spec_files

# Generate all specs
generate_spec_files(base_dir="/path/to/reflex", specs_dir="specs")

# Or just common props
from spec_generator import generate_common_props_spec
generate_common_props_spec(specs_dir="specs")
```

## Features & Improvements

The generator includes several specific enhancements:

1. **Property Name Standardization**: Properly handles special property names like `_as` instead of `as_`
2. **Enum Value Extraction**: Converts descriptions like `"1" - "9"` to proper enum values arrays
3. **Component Filtering**: Filters out invalid or test components
4. **Description Cleaning**: Removes enum formats from descriptions for cleaner output
5. **Organized Mapping**: Components are organized into logical mapping modules:
   - Base components (base.py)
   - Specialized components (specialized.py)
   - AG Grid components (ag_grid.py)
   - Radix UI components (radix.py)
   - Core and other components (core.py)

## Package Structure

The codebase is organized into several modules:

- `spec_generator.mapping`: Functions for mapping component names to file paths
- `spec_generator.extraction`: Functions for extracting component information
- `spec_generator.output`: Functions for generating and saving spec files
- `spec_generator.utils`: Utility functions
- `spec_generator.discovery`: Functions for discovering components
- `spec_generator.cli`: Command-line interface

## Output

The generated specs are saved as JSON files in the `specs` directory (or a directory specified with `--specs-dir`). Each component has its own spec file, and there's also a `common_props.json` file for common properties shared by most components.
