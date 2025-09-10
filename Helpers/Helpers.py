def is_correct_color(value) -> bool:
    if isinstance(value, tuple) and len(value) == 3:
        return all(isinstance(i, int) for i in value)
    return False

def get_element_by_index(arr, index):
    if 0 <= index < len(arr):
        return arr[index]
    return None

def get_trand(current_value, preview_value) -> str:
    # Handle error states and None values
    if current_value in ["No temp sensor", "ERROR", None] or preview_value in ["No temp sensor", "ERROR", None]:
        return ""
    
    # Handle string values
    if isinstance(current_value, str) or isinstance(preview_value, str):
        return ""
    
    # Handle numeric comparison
    try:
        current_float = float(current_value)
        preview_float = float(preview_value)
        
        if current_float < preview_float:
            return "down"
        elif current_float > preview_float:
            return "up"
        else:
            return ""
    except (ValueError, TypeError):
        return ""