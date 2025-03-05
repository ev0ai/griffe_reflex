"""
Functions for extracting event handlers from component class bodies.
"""
import re
from typing import Dict, Any, List, Set

# Common event handlers used by most components
COMMON_EVENT_HANDLERS = [
    "on_focus", "on_blur", "on_change", "on_click", "on_context_menu", "on_double_click",
    "on_mouse_down", "on_mouse_enter", "on_mouse_leave", "on_mouse_move", "on_mouse_out",
    "on_mouse_over", "on_mouse_up", "on_scroll", "on_key_down", "on_key_press", "on_key_up"
]

def extract_event_handlers(class_body: str) -> List[str]:
    """Extract event handlers from a class body.
    
    Args:
        class_body: The class body to extract event handlers from
        
    Returns:
        A list of event handler names
    """
    # Look for event handler properties like "on_click: Callable = ..."
    event_pattern = r'^\s*on_\w+\s*:'
    
    events = []
    for line in class_body.splitlines():
        if re.search(event_pattern, line):
            # Extract the event name (e.g., "on_click")
            event_match = re.search(r'^\s*(\w+)\s*:', line)
            if event_match:
                event_name = event_match.group(1)
                events.append(event_name)
    
    return events

def extract_common_events() -> Set[str]:
    """Get a set of common event handler names.
    
    Returns:
        A set of common event handler names
    """
    return set(COMMON_EVENT_HANDLERS) 