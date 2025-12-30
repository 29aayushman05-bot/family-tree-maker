def initialize_tree():
    """Initialize empty tree structure"""
    return {
        'nodes': [],
        'edges': []
    }

def format_date_range(birth_date, death_date=''):
    """Format date range for display (birth-death)"""
    if not birth_date and not death_date:
        return ''
    
    # Handle single date field (backward compatibility)
    if birth_date and not death_date:
        # Check if it's just a year or full date
        birth_display = birth_date.strip()
        if len(birth_display) == 4 and birth_display.isdigit():
            return f"{birth_display}-"
        elif birth_date:
            return f"{birth_display}-"
        return birth_display
    
    # Handle both dates
    birth_display = birth_date.strip() if birth_date else ''
    death_display = death_date.strip() if death_date else ''
    
    if birth_display and death_display:
        return f"{birth_display}-{death_display}"
    elif birth_display:
        return f"{birth_display}-"
    elif death_display:
        return f"-{death_display}"
    
    return ''
