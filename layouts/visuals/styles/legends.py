# layouts/visuals/styles/legend_styles.py
# =======================================
# 🎨 Catálogo de estilos de leyenda (Plotly/Dash)
# ------------------------------------------------
# Cada estilo define una configuración visual distinta.
# Puedes importar `legend_styles_dict` y pasar el estilo deseado a `layout.legend`.

# 🧱 Estilo clásico horizontal (debajo del gráfico)
from operator import le


legend_style_classic = dict(
    bgcolor='rgba(255,255,255,0.7)',
    bordercolor='rgba(0,0,0,0.3)',
    borderwidth=1,
    orientation="h",
    yanchor="bottom",
    y=-0.25,
    xanchor="center",
    x=0.5
)

# 🌤 Estilo claro flotante (superior derecha)
legend_style_light_top_right = dict(
    bgcolor='rgba(255,255,255,0.8)',
    bordercolor='rgba(200,200,200,0.5)',
    borderwidth=1,
    orientation="v",
    x=1.02,
    xanchor="left",
    y=1,
    yanchor="top"
)

# 🌑 Estilo oscuro transparente (dentro del gráfico)
legend_style_dark_overlay = dict(
    bgcolor='rgba(0,0,0,0.6)',
    bordercolor='rgba(255,255,255,0.2)',
    borderwidth=1,
    font=dict(color='white'),
    x=0.02,
    xanchor="left",
    y=0.98,
    yanchor="top"
)

# 🌈 Estilo minimalista sin fondo ni borde
legend_style_minimal = dict(
    bgcolor='rgba(0,0,0,0)',
    bordercolor='rgba(0,0,0,0)',
    borderwidth=0,
    font=dict(size=12),
    x=0.5,
    y=1.05,
    xanchor="center",
    yanchor="bottom",
    orientation="h"
)

# 💎 Estilo “tarjeta” moderna centrada
legend_style_card_centered = dict(
    bgcolor='rgba(245,245,245,0.9)',
    bordercolor='rgba(180,180,180,0.8)',
    borderwidth=1,
    font=dict(size=13, color='#222'),
    orientation="h",
    x=0.5,
    y=-0.2,
    xanchor="center",
    yanchor="top"
)

# 🧊 Estilo profesional azul
legend_style_professional = dict(
    bgcolor='rgba(25,25,35,0.95)',
    bordercolor='rgba(0,150,255,0.7)',
    borderwidth=2,
    font=dict(size=12, color='white'),
    x=1.02,
    xanchor="left",
    y=1,
    yanchor="top"
)

# 🧩 Estilo vertical lateral izquierdo
legend_style_left_vertical = dict(
    bgcolor='rgba(255,255,255,0.8)',
    bordercolor='rgba(120,120,120,0.4)',
    borderwidth=1,
    orientation="v",
    x=-0.2,
    xanchor="right",
    y=0.5,
    yanchor="middle"
)

# 🪩 Estilo retro terminal
legend_style_terminal = dict(
    bgcolor='rgba(0,20,0,0.9)',
    bordercolor='rgba(0,255,0,0.5)',
    borderwidth=1,
    font=dict(color='rgb(0,255,0)'),
    x=0.02,
    y=0.98,
    xanchor="left",
    yanchor="top"
)

# 🧨 Estilo alerta (rojo con texto blanco)
legend_style_alert = dict(
    bgcolor='rgba(255,60,60,0.8)',
    bordercolor='rgba(255,255,255,0.6)',
    borderwidth=2,
    font=dict(color='white', size=13),
    x=0.98,
    y=0.02,
    xanchor="right",
    yanchor="bottom"
)

# 📊 Estilo compacto para dashboards
legend_style_compact = dict(
    bgcolor='rgba(255,255,255,0.6)',
    bordercolor='rgba(0,0,0,0.1)',
    borderwidth=1,
    font=dict(size=10),
    orientation="h",
    x=0.5,
    y=-0.15,
    xanchor="center",
    yanchor="top"
)

legend_style_profesional_overtop = dict(
    bgcolor='rgba(255, 255, 255, 0.95)',
    bordercolor='#8893fe',
    borderwidth=3,
    font=dict(size=10, color='#222222', weight='bold'),
    orientation="h",
    itemwidth=30,           # Ancho del símbolo (la línea de color)
    tracegroupgap=5,        # Espacio vertical entre grupos
    x=0.5,
    y=1.05,
    xanchor="center",
    yanchor="bottom"
)

legend_style_vertical_list = dict(
    bgcolor='rgba(255, 255, 255, 0.85)', # Fondo semi-transparente
    bordercolor='#8893fe',               # Tu color lila de borde
    borderwidth=1,
    orientation="v",                     # <--- CLAVE: Vertical (Columna)
    yanchor="top",
    y=1,                                 # Alineado arriba
    xanchor="left",
    x=1.01,                              # Justo a la derecha del gráfico (fuera)
    # x=0.01,                            # (Opcional) Usa esto si la quieres DENTRO a la izquierda
    font=dict(size=11, color='#222'),
    itemwidth=30,                        # Iconos más pegados
    tracegroupgap=5                      # Espacio reducido entre items
)

# 🧠 Diccionario con todos los estilos
legend_styles_dict = {
    "classic": legend_style_classic,
    "light_top_right": legend_style_light_top_right,
    "dark_overlay": legend_style_dark_overlay,
    "minimal": legend_style_minimal,
    "card_centered": legend_style_card_centered,
    "professional": legend_style_professional,
    "left_vertical": legend_style_left_vertical,
    "terminal": legend_style_terminal,
    "alert": legend_style_alert,
    "compact": legend_style_compact,
    "profesional_overtop": legend_style_profesional_overtop,
    "vertical_list": legend_style_vertical_list, # <--- AÑADIR AQUÍ
}


