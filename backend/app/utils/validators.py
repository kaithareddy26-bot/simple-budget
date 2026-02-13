import re
from datetime import datetime
from typing import Tuple


def validate_month_format(month: str) -> Tuple[bool, str]:
    """
    Validate month format (YYYY-MM).
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not re.match(r'^\d{4}-\d{2}$', month):
        return False, "Month must be in YYYY-MM format"
    
    try:
        year, month_num = month.split('-')
        year_int = int(year)
        month_int = int(month_num)
        
        if not (1 <= month_int <= 12):
            return False, "Month must be between 01 and 12"
        
        if year_int < 1900 or year_int > 2100:
            return False, "Year must be between 1900 and 2100"
        
        return True, ""
    except ValueError:
        return False, "Invalid month format"


def parse_month(month: str) -> datetime:
    """Parse month string to datetime object."""
    return datetime.strptime(month, "%Y-%m")


def get_month_range(month: str) -> Tuple[datetime, datetime]:
    """
    Get the start and end datetime for a given month.
    
    Args:
        month: Month string in YYYY-MM format
        
    Returns:
        Tuple of (start_date, end_date)
    """
    date_obj = parse_month(month)
    year = date_obj.year
    month_num = date_obj.month
    
    # Start of month
    start_date = datetime(year, month_num, 1)
    
    # End of month
    if month_num == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month_num + 1, 1)
    
    return start_date, end_date
