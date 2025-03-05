from typing import Dict, Any


def get_specialized_mappings(base_dir: str) -> Dict[str, Dict[str, str]]:
    """Get mappings for specialized components.
    
    Args:
        base_dir: Base directory of the Reflex codebase
        
    Returns:
        A dictionary of component names to their module paths and file paths.
    """
    return {
        # Components that live in nested directories
        "audio": {
            "module_path": "components.react_player.react_player",
            "file_path": f"{base_dir}/reflex/reflex/components/react_player/react_player.py"
        },
        "video": {
            "module_path": "components.react_player.react_player",
            "file_path": f"{base_dir}/reflex/reflex/components/react_player/react_player.py"
        },
        "icon": {
            "module_path": "components.lucide.icon",
            "file_path": f"{base_dir}/reflex/reflex/components/lucide/icon.py"
        },
        "moment": {
            "module_path": "components.moment.moment",
            "file_path": f"{base_dir}/reflex/reflex/components/moment/moment.py"
        },
        "markdown": {
            "module_path": "components.markdown.markdown",
            "file_path": f"{base_dir}/reflex/reflex/components/markdown/markdown.py"
        },
        "editor": {
            "module_path": "components.suneditor.suneditor",
            "file_path": f"{base_dir}/reflex/reflex/components/suneditor/suneditor.py"
        },
        "data_table": {
            "module_path": "components.gridjs.gridjs",
            "file_path": f"{base_dir}/reflex/reflex/components/gridjs/gridjs.py"
        },
        # Special components that need specific handling
        "areachart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "barchart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "composedchart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "linechart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "piechart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "radarchart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "radialbarchart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "scatterchart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "funnelchart": {
            "module_path": "components.recharts.charts",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/charts.py"
        },
        "legend": {
            "module_path": "components.recharts.general",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/general.py"
        },
        "recharts": {
            "module_path": "components.recharts.general",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/general.py"
        },
        "axis": {
            "module_path": "components.recharts.cartesian",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/cartesian.py"
        },
        "brush": {
            "module_path": "components.recharts.cartesian",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/cartesian.py"
        },
        "cartesiangrid": {
            "module_path": "components.recharts.cartesian",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/cartesian.py"
        },
        "errorbar": {
            "module_path": "components.recharts.cartesian",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/cartesian.py"
        },
        "reference": {
            "module_path": "components.recharts.cartesian",
            "file_path": f"{base_dir}/reflex/reflex/components/recharts/cartesian.py"
        }
    } 