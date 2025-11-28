"""
Parameter validation utilities.
"""

def validate_positive_float(value: float, name: str) -> float:
    """
    Validate that a value is a positive float.
    
    Args:
        value: Value to validate
        name: Name of the variable for error message
        
    Returns:
        The validated value
        
    Raises:
        ValueError: If value is not positive
    """
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value

def validate_percentage(value: float, name: str) -> float:
    """
    Validate that a value is a percentage (0-100).
    
    Args:
        value: Value to validate
        name: Name of the variable for error message
        
    Returns:
        The validated value
        
    Raises:
        ValueError: If value is not between 0 and 100
    """
    if not 0 <= value <= 100:
        raise ValueError(f"{name} must be between 0 and 100")
    return value
