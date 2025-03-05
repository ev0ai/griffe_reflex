# Reflex Component Specification Generator

This tool extracts component specifications from the Reflex codebase and generates JSON files that can be used for documentation, code generation, and IDE integrations.

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
