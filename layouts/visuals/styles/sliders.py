# layouts/visuals/styles/slider.py
# ==================================
# 🎨 Ejemplos de estilos de rangeslider para Plotly/Dash

# -----------------------------------------------------
# 🧱 Ejemplo base: fino, oscuro, discreto
slider_style_dark_minimal = dict(
    visible=True,
    thickness=0.05,
    bgcolor='rgba(30,30,30,0.9)',
    bordercolor='rgba(255,255,255,0.3)',
    borderwidth=1
)

# 🌤 Ejemplo claro y elegante
slider_style_light = dict(
    visible=True,
    thickness=0.07,
    bgcolor='rgba(240,240,240,1)',
    bordercolor='rgba(200,200,200,1)',
    borderwidth=1
)

# 🌈 Ejemplo con degradado (nota: no nativo, efecto visual simulado)
slider_style_gradient = dict(
    visible=True,
    thickness=0.1,
    bgcolor='rgba(0,123,255,0.3)',  # degradado no soportado directamente
    bordercolor='rgba(255,255,255,0.5)',
    borderwidth=2
)

# ⚫ Estilo "neón" oscuro con borde brillante
slider_style_neon = dict(
    visible=True,
    thickness=0.08,
    bgcolor='rgba(0,0,0,0.8)',
    bordercolor='rgba(0,255,150,0.9)',
    borderwidth=2
)

# 📉 Estilo ultra fino (minimalista total)
slider_style_thin = dict(
    visible=True,
    thickness=0.02,
    bgcolor='rgba(100,100,100,0.5)',
    bordercolor='rgba(255,255,255,0.2)',
    borderwidth=0
)

# 🧊 Estilo profesional con toque azul
slider_style_professional = dict(
    visible=True,
    thickness=0.06,
    bgcolor='rgba(25,25,25,0.9)',
    bordercolor='rgba(0,150,255,0.6)',
    borderwidth=1
)

slider_style_professional2 = dict(
    visible=True,
    thickness=0.06,
    bgcolor="#e8ebfd",
    bordercolor='#8893fe',
    borderwidth=2
)

# 💎 Estilo elegante translúcido
slider_style_glass = dict(
    visible=True,
    thickness=0.08,
    bgcolor='rgba(255,255,255,0.3)',
    bordercolor='rgba(255,255,255,0.7)',
    borderwidth=1
)

# 🧨 Estilo "alerta" rojo
slider_style_alert = dict(
    visible=True,
    thickness=0.1,
    bgcolor='rgba(255,60,60,0.8)',
    bordercolor='rgba(255,255,255,0.6)',
    borderwidth=2
)

# 🪩 Estilo retro “terminal”
slider_style_terminal = dict(
    visible=True,
    thickness=0.07,
    bgcolor='rgba(0,20,0,0.9)',
    bordercolor='rgba(0,255,0,0.5)',
    borderwidth=1
)

# 🧠 Diccionario para importar fácilmente
slider_styles_dict = {
    "dark_minimal": slider_style_dark_minimal,
    "light": slider_style_light,
    "gradient": slider_style_gradient,
    "neon": slider_style_neon,
    "thin": slider_style_thin,
    "professional": slider_style_professional,
    "professional2": slider_style_professional2,
    "glass": slider_style_glass,
    "alert": slider_style_alert,
    "terminal": slider_style_terminal,
}
