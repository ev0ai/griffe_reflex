import os
import re
from typing import Dict, Any


def extract_component_mappings(base_dir: str) -> Dict[str, Dict[str, str]]:
    """Extract component mappings from reflex/reflex/components/__init__.pyi.
    
    Args:
        base_dir: Base directory of the Reflex codebase
        
    Returns:
        A dictionary of component names to their module paths and file paths.
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


def get_base_mappings(base_dir: str) -> Dict[str, Dict[str, str]]:
    """Get mappings for base components.
    
    Args:
        base_dir: Base directory of the Reflex codebase
        
    Returns:
        A dictionary of component names to their module paths and file paths.
    """
    return extract_component_mappings(base_dir) 