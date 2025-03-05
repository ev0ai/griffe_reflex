"""
Specification generator for Reflex components.

This package provides tools for extracting component specifications from the
Reflex codebase. The specifications are saved as JSON files that can be used
for documentation, code generation, and IDE integrations.
"""

__version__ = "0.1.0"

from spec_generator.cli import main
from spec_generator.discovery import find_all_components
from spec_generator.output import generate_spec_files, generate_common_props_spec

__all__ = [
    "main",
    "find_all_components",
    "generate_spec_files",
    "generate_common_props_spec",
]
