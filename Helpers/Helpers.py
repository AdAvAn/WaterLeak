def is_correct_color(value) -> bool:
    if isinstance(value, tuple) and len(value) == 3:
        return all(isinstance(i, int) for i in value)
    return False

def get_element_by_index(arr, index):
    if 0 <= index < len(arr):
        return arr[index]
    return None

def get_trand(current_value, preview_value) -> str:
    if preview_value and current_value:
        if isinstance(preview_value, str) or isinstance(current_value, str):
            return ""
        else:
            return "down" if current_value < preview_value else "up"
    else:
        return "" 