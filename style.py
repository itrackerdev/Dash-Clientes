# style.py

COLORS = {
    'primary': '#1E88E5',
    'secondary': '#26A69A',
    'success': '#66BB6A',
    'warning': '#FFA726',
    'danger': '#EF5350',
    'background': '#F8F9FA',
    'text': '#212529',
    'light_text': '#6C757D',
    'chart1': ['#1E88E5', '#26A69A', '#66BB6A'],
    'chart2': ['#42A5F5', '#7E57C2', '#26A69A', '#EC407A', '#FFA726']
}

def get_css(theme, colors=COLORS):
    if theme == "Escuro":
        background_color = "#121212"
        secondary_background = "#1E1E1E"
        text_color = "#FFFFFF"
        light_text = "#CCCCCC"
    elif theme == "Clean":
        background_color = "#FFFFFF"
        secondary_background = "#F0F0F0"
        text_color = "#212529"
        light_text = "#6C757D"
    else:  # Claro
        background_color = colors['background']
        secondary_background = "#ffffff"
        text_color = colors['text']
        light_text = colors['light_text']

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        body, .block-container {{
            font-family: 'Inter', sans-serif;
            background-color: {background_color};
            color: {text_color};
        }}
        .main {{
            background-color: {background_color};
            padding: 20px;
            animation: fadeIn 1s;
        }}
        .section {{
            background-color: {secondary_background};
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.08);
            margin-bottom: 20px;
        }}
        .kpi-card {{
            background-color: {secondary_background};
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 3px 6px rgba(0,0,0,0.1);
            text-align: center;
            border-left: 5px solid {colors['primary']};
        }}
        .kpi-card:nth-child(2) {{
            border-left-color: {colors['warning']};
        }}
        .kpi-card:nth-child(3) {{
            border-left-color: {colors['success']};
        }}
        .kpi-card:nth-child(4) {{
            border-left-color: {colors['danger']};
        }}
        .kpi-title {{
            font-size: 14px;
            margin-bottom: 5px;
            color: {text_color};
        }}
        .kpi-value {{
            font-size: 24px;
            font-weight: bold;
            color: {text_color};
        }}
        .section-title {{
            color: {text_color};
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 15px;
            border-bottom: 2px solid {light_text};
            padding-bottom: 8px;
        }}
        .sub-title {{
            color: {text_color};
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        .sidebar .sidebar-content {{
            background-color: {secondary_background};
        }}
        .stButton>button {{
            background-color: {colors['primary']};
            color: white;
            border-radius: 5px;
            border: none;
            padding: 8px 16px;
            font-weight: 500;
        }}
        .stButton>button:hover {{
            background-color: #1976D2;
        }}
        .divider {{
            margin-top: 20px;
            margin-bottom: 20px;
            border-top: 1px solid {light_text};
        }}
        @keyframes fadeIn {{
          from {{ opacity: 0; }}
          to {{ opacity: 1; }}
        }}
        .custom-footer {{
            text-align: center;
            padding: 10px;
            border-top: 1px solid {light_text};
            font-size: 13px;
            color: {light_text};
            margin-top: 20px;
        }}
        .custom-footer span {{
            margin: 0 5px;
        }}
        /* Cabeçalho com cor institucional fixa (laranja e branco) */
        .titulo-dashboard-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
            margin: 40px auto;
            padding: 25px 20px;
            background: linear-gradient(to right, #F37529, rgba(255, 255, 255, 0.8));
            border-radius: 15px;
            box-shadow: 0 6px 10px rgba(0, 0, 0, 0.3);
        }}
        .titulo-dashboard {{
            font-size: 50px;
            font-weight: bold;
            color: #F37529;
            text-transform: uppercase;
            margin: 0;
        }}
        .subtitulo-dashboard {{
            font-size: 18px;
            color: {light_text};
            margin: 10px 0 0 0;
        }}
    </style>
    """
    return css
