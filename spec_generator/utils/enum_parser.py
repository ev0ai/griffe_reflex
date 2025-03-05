import re
from typing import List, Optional


def extract_enum_values_from_description(description: str) -> Optional[List[str]]:
    """Extract enum values from description strings like 'Options: "value1" | "value2" | "value3"'
    or 'Text size: "1" - "9"'
    
    Args:
        description: The property description string that may contain enum values
        
    Returns:
        A list of enum values if found, otherwise None
    """
    # Check for numeric range pattern like "1" - "9"
    range_match = re.search(r'"(\d+)"\s*-\s*"(\d+)"', description)
    if range_match:
        start = int(range_match.group(1))
        end = int(range_match.group(2))
        return [str(i) for i in range(start, end + 1)]
    
    # Find patterns like "value1" | "value2" | "value3"
    enum_match = re.search(r'(?:"([^"]+)"(?:\s*\|\s*"([^"]+)")+)', description)
    if enum_match:
        # Extract all double-quoted values
        values = re.findall(r'"([^"]+)"', description)
        return values
    return None 