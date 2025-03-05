import re
from typing import List, Optional


def extract_enum_values_from_description(description: str) -> Optional[List[str]]:
    """Extract enum values from description strings like 'Options: "value1" | "value2" | "value3"'
    
    Args:
        description: The property description string that may contain enum values
        
    Returns:
        A list of enum values if found, otherwise None
    """
    # Find patterns like "value1" | "value2" | "value3"
    enum_match = re.search(r'(?:"([^"]+)"(?:\s*\|\s*"([^"]+)")+)', description)
    if enum_match:
        # Extract all double-quoted values
        values = re.findall(r'"([^"]+)"', description)
        return values
    return None 