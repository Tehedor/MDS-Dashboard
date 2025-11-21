# layouts/visuals/slider_style.py
from .styles.sliders import slider_styles_dict

def get_slider_style(slider_min=None, slider_max=None):
    """Define el estilo visual del rangeslider (línea temporal inferior)."""

    # style_name = "dark_minimal"
    # style_name = "light"
    # style_name = "gradient"
    # style_name = "neon"
    # style_name = "thin"
    style_name = "professional2"
    # style_name = "glass"
    # style_name = "alert"
    # style_name = "terminal"

    style = dict(slider_styles_dict.get(style_name, {}).copy())   


    if slider_min is not None and slider_max is not None:
        style["range"] = [slider_min, slider_max]

    return style


# slider_styles_dict = {
#     "dark_minimal": slider_style_dark_minimal,
#     "light": slider_style_light,
#     "gradient": slider_style_gradient,
#     "neon": slider_style_neon,
#     "thin": slider_style_thin,
#     "professional": slider_style_professional,
#     "glass": slider_style_glass,
#     "alert": slider_style_alert,
#     "terminal": slider_style_terminal,
# }
