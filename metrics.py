# metrics.py

import pandas as pd

def format_number(num):
    if num >= 1000000:
        return f"{num/1000000:.2f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return f"{num:.0f}"

def format_percent(value, positive_is_good=True):
    if value is None or pd.isna(value):
        return "N/A"
    if value >= 100:
        color = "green" if positive_is_good else "red"
        return f"<span style='color:{color};font-weight:bold'>{value:.1f}%</span>"
    elif value >= 70:
        return f"<span style='color:orange;font-weight:bold'>{value:.1f}%</span>"
    else:
        color = "red" if positive_is_good else "green"
        return f"<span style='color:{color};font-weight:bold'>{value:.1f}%</span>"

def custom_round(x):
    frac = x - int(x)
    if frac > 0.5:
        return int(x) + 1
    else:
        return int(x)
