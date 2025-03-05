from typing import Dict, Any


def get_core_mappings(base_dir: str) -> Dict[str, Dict[str, str]]:
    """Get mappings for core and other components.
    
    Args:
        base_dir: Base directory of the Reflex codebase
        
    Returns:
        A dictionary of component names to their module paths and file paths.
    """
    return {
        # Code and data components
        "code_block": {
            "module_path": "components.datadisplay.code",
            "file_path": f"{base_dir}/reflex/reflex/components/datadisplay/code.py"
        },
        "data_editor": {
            "module_path": "components.datadisplay.dataeditor",
            "file_path": f"{base_dir}/reflex/reflex/components/datadisplay/dataeditor.py"
        },
        
        # Element components
        "el": {
            "module_path": "components.el",
            "file_path": f"{base_dir}/reflex/reflex/components/el/__init__.py"
        },
        "list": {
            "module_path": "components.el.elements.list",
            "file_path": f"{base_dir}/reflex/reflex/components/el/elements/list.py"
        },
        "image": {
            "module_path": "components.el.elements.media",
            "file_path": f"{base_dir}/reflex/reflex/components/el/elements/media.py"
        },
        "html_embed": {
            "module_path": "components.el.elements.embed",
            "file_path": f"{base_dir}/reflex/reflex/components/el/elements/embed.py"
        },
        
        # Core components
        "clipboard": {
            "module_path": "components.core.clipboard",
            "file_path": f"{base_dir}/reflex/reflex/components/core/clipboard.py"
        },
        "cond": {
            "module_path": "components.core.cond",
            "file_path": f"{base_dir}/reflex/reflex/components/core/cond.py"
        },
        "foreach": {
            "module_path": "components.core.foreach",
            "file_path": f"{base_dir}/reflex/reflex/components/core/foreach.py"
        },
        "match": {
            "module_path": "components.core.match",
            "file_path": f"{base_dir}/reflex/reflex/components/core/match.py"
        },
        "upload": {
            "module_path": "components.core.upload",
            "file_path": f"{base_dir}/reflex/reflex/components/core/upload.py"
        },
        
        # Base components
        "fragment": {
            "module_path": "components.base.fragment",
            "file_path": f"{base_dir}/reflex/reflex/components/base/fragment.py"
        },
        "script": {
            "module_path": "components.base.script",
            "file_path": f"{base_dir}/reflex/reflex/components/base/script.py"
        },
        
        # Sonner components
        "toast": {
            "module_path": "components.sonner.toast",
            "file_path": f"{base_dir}/reflex/reflex/components/sonner/toast.py"
        }
    } 