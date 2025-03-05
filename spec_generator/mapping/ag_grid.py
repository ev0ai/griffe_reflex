from typing import Dict, Any


def get_ag_grid_mappings(base_dir: str) -> Dict[str, Dict[str, str]]:
    """Get mappings for AG Grid components.
    
    Args:
        base_dir: Base directory of the Reflex codebase
        
    Returns:
        A dictionary of component names to their module paths and file paths.
    """
    return {
        "ag_grid": {
            "module_path": "components.ag_grid.ag_grid",
            "file_path": f"{base_dir}/reflex/reflex/components/ag_grid/ag_grid.py"
        }
    } 