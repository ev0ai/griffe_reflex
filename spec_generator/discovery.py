from typing import Dict, Any

from spec_generator.mapping import (
    get_base_mappings,
    get_specialized_mappings,
    get_ag_grid_mappings,
    get_radix_mappings,
    get_core_mappings
)


def find_all_components(base_dir: str) -> Dict[str, Dict[str, str]]:
    """Find all components in the codebase.
    
    Args:
        base_dir: Base directory of the Reflex codebase
        
    Returns:
        A dictionary of component names to their module paths and file paths.
    """
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
    
    # Filter out invalid components
    invalid_components = ["component", "next_link", "nextlink", "nossrcomponent"]
    for invalid_comp in invalid_components:
        if invalid_comp in components:
            del components[invalid_comp]
    
    # Filter out components with spaces in their names
    # Filter them by creating a new dict without those components
    components = {k: v for k, v in components.items() if ' as ' not in k}
    
    print(f"Found {len(components)} components")
    
    return components 