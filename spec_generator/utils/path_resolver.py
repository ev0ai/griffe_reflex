import os
from pathlib import Path
from typing import Optional, List


def ensure_directory_exists(directory: str) -> None:
    """Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory: The directory path to ensure exists
    """
    os.makedirs(directory, exist_ok=True)


def find_file_in_directories(filename: str, directories: List[str]) -> Optional[str]:
    """Search for a file in multiple directories.
    
    Args:
        filename: The name of the file to search for
        directories: List of directories to search in
        
    Returns:
        The full path to the file if found, otherwise None
    """
    for directory in directories:
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            return filepath
    return None


def get_reflex_component_path(base_dir: str, component_name: str) -> str:
    """Get the expected path for a Reflex component.
    
    Args:
        base_dir: Base directory of the Reflex codebase
        component_name: Name of the component
        
    Returns:
        The expected path to the component
    """
    return os.path.join(base_dir, "reflex", "reflex", "components", f"{component_name}.py")


def get_output_path(output_dir: str, component_name: str) -> str:
    """Get the output path for a component specification.
    
    Args:
        output_dir: Directory to output specifications
        component_name: Name of the component
        
    Returns:
        The full path for the component specification
    """
    return os.path.join(output_dir, f"{component_name}.json") 