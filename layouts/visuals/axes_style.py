from .styles.axes import axes_styles_dict

def get_axes_style(x_min=None, x_max=None, slider_style=None):
    """Define la configuración visual de los ejes X e Y."""
    
    style_name = "professional"  # Cambia según prefieras
    
    # ✅ Obtener la FUNCIÓN del diccionario y llamarla con los parámetros
    style_function = axes_styles_dict.get(style_name)
    
    if style_function:
        return style_function(x_min=x_min, x_max=x_max, slider_style=slider_style)
    else:
        # Fallback: estilo por defecto
        return {
            'xaxis': {
                'type': 'date',
                'range': [x_min, x_max] if x_min else None,
                'rangeslider': slider_style or {},
                'showgrid': True,
                'gridcolor': 'rgba(123, 130, 203, 0.3)',
                'zerolinecolor': 'rgba(123, 130, 203, 0.5)'
            },
            'yaxis': {
                'autorange': True,
                'showgrid': True,
                'gridcolor': 'rgba(123, 130, 203, 0.2)'
            }
        }