import pandas as pd

def sum_finder(data_frame, col_name):
    # Calculate the total sum of the specified column
    total = data_frame[col_name].sum()
    # Check if total is 1000 or more
    if total >= 1000:
        total_k = total / 1000
        # Return formatted value with or without decimal based on its value
        return f"{total_k:.0f}K" if total_k.is_integer() else f"{total_k:.2f}K"
    
    return total