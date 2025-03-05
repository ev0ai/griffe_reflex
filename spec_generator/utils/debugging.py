from typing import Any


def print_debug(*args: Any, **kwargs: Any) -> None:
    """Debug print function that can be enabled/disabled globally.
    
    Args:
        *args: Arguments to print
        **kwargs: Keyword arguments for print function
    """
    # Change DEBUG to True to enable debug printing
    DEBUG = False
    
    if DEBUG:
        print(*args, **kwargs) 