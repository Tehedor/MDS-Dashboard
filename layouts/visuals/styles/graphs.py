# layouts/visuals/styles/graph_styles.py
# ======================================
# 🎨 Catálogo de estilos globales de layout para figuras Plotly/Dash.
# Cada estilo define colores, fondos, fuentes y comportamiento del hover.
# Se combinan con los estilos de ejes, leyenda y slider.

# 🧱 Estilo claro clásico (default)
graph_style_classic = dict(
    plot_bgcolor="#F8F9FA",
    paper_bgcolor="#FFFFFF",
    hovermode='x unified',
    font=dict(
        family='Arial, sans-serif',
        size=14,
        color='#000000'
    ),
    margin=dict(l=50, r=30, t=50, b=50),
    hoverlabel=dict(
        bgcolor='rgba(240,240,240,0.9)',
        font_size=13,
        font_color='#000'
    )
)

# 🌑 Estilo oscuro moderno
graph_style_dark = dict(
    plot_bgcolor="#121212",
    paper_bgcolor="#181818",
    font=dict(
        family='Roboto, sans-serif',
        size=14,
        color='#EAEAEA'
    ),
    hovermode='x unified',
    hoverlabel=dict(
        bgcolor='rgba(40,40,40,0.9)',
        font_color='white'
    ),
    margin=dict(l=50, r=30, t=50, b=50),
)

# 💎 Estilo profesional azul
graph_style_professional = dict(
    plot_bgcolor='rgba(20,30,50,1)',
    paper_bgcolor='rgba(15,20,30,1)',
    font=dict(
        family='Open Sans, sans-serif',
        size=15,
        color='rgba(220,230,255,0.95)',
    ),
    hovermode='x unified',
    hoverlabel=dict(
        bgcolor='rgba(0,100,255,0.9)',
        font_color='white',
        bordercolor='rgba(255,255,255,0.3)',
    ),
    margin=dict(l=60, r=40, t=60, b=60),
)

# 🌈 Estilo con gradiente de fondo
graph_style_gradient = dict(
    plot_bgcolor='rgba(255,255,255,0)',
    paper_bgcolor='linear-gradient(90deg, #e0eafc 0%, #cfdef3 100%)',  # decorativo
    font=dict(
        family='Lato, sans-serif',
        size=15,
        color='#222'
    ),
    hovermode='x unified',
    hoverlabel=dict(
        bgcolor='rgba(255,255,255,0.8)',
        font_color='#000'
    )
)

# 🪩 Estilo retro “terminal”
graph_style_terminal = dict(
    plot_bgcolor='rgba(0,20,0,1)',
    paper_bgcolor='rgba(0,15,0,1)',
    font=dict(
        family='Courier New, monospace',
        size=13,
        color='rgb(0,255,0)'
    ),
    hovermode='x unified',
    hoverlabel=dict(
        bgcolor='rgba(0,40,0,0.9)',
        font_color='rgb(0,255,0)',
        bordercolor='rgba(0,255,0,0.5)',
    ),
    margin=dict(l=50, r=30, t=50, b=50)
)

# 🌤 Estilo “glass” translúcido (para dashboards con fondo difuminado)
graph_style_glass = dict(
    plot_bgcolor='rgba(255,255,255,0.2)',
    paper_bgcolor='rgba(255,255,255,0.15)',
    font=dict(
        family='Segoe UI, sans-serif',
        size=14,
        color='#111'
    ),
    hovermode='x unified',
    hoverlabel=dict(
        bgcolor='rgba(255,255,255,0.6)',
        font_color='#000'
    ),
    margin=dict(l=60, r=40, t=50, b=50)
)

# 🧠 Estilo minimalista (sin bordes, tipografía limpia)
graph_style_minimal = dict(
    plot_bgcolor='#FFFFFF',
    paper_bgcolor='#FFFFFF',
    font=dict(
        family='Inter, sans-serif',
        size=13,
        color='#111'
    ),
    hovermode='closest',
    hoverlabel=dict(
        bgcolor='rgba(255,255,255,0.9)',
        font_color='#111'
    ),
    margin=dict(l=40, r=30, t=40, b=40),
    showlegend=False
)

# 🧨 Estilo alerta / diagnóstico (fondos cálidos)
graph_style_alert = dict(
    plot_bgcolor='rgba(255,230,230,1)',
    paper_bgcolor='rgba(255,240,240,1)',
    font=dict(
        family='Arial, sans-serif',
        size=14,
        color='rgba(100,0,0,1)',
        weight='bold'
    ),
    hovermode='x unified',
    hoverlabel=dict(
        bgcolor='rgba(255,100,100,0.8)',
        font_color='white'
    ),
    margin=dict(l=50, r=30, t=50, b=50),
)

# 🧊 Estilo científico (para gráficos de datos técnicos)
graph_style_scientific = dict(
    plot_bgcolor='#F4F6F9',
    paper_bgcolor='#F9FAFB',
    font=dict(
        family='IBM Plex Sans, sans-serif',
        size=14,
        color='#111'
    ),
    hovermode='x unified',
    hoverlabel=dict(
        bgcolor='rgba(230,230,255,0.9)',
        font_color='#000'
    ),
    margin=dict(l=70, r=40, t=60, b=60),
    xaxis_showgrid=True,
    yaxis_showgrid=True,
)

# 📊 Estilo compacto (para dashboards apretados)
graph_style_compact = dict(
    plot_bgcolor='#FFFFFF',
    paper_bgcolor='#FFFFFF',
    font=dict(
        family='Arial Narrow, sans-serif',
        size=11,
        color='#000'
    ),
    hovermode='x unified',
    hoverlabel=dict(
        bgcolor='rgba(255,255,255,0.9)',
        font_color='#000'
    ),
    margin=dict(l=30, r=20, t=30, b=30)
)


# 🌤 Estilo "glass" translúcido (para dashboards con fondo difuminado)
graph_style_glass1 = dict(
    plot_bgcolor='rgba(247, 247, 249, 0.95)',  # Fondo más claro y sólido
    paper_bgcolor='rgba(255, 255, 255, 0.98)',  # Papel casi blanco
    font=dict(
        family='Segoe UI, sans-serif',
        size=14,
        color='#111',
        weight='bold'  # Negrita
    ),
    hovermode='x unified',
    hoverlabel=dict(
        bgcolor='rgba(255,255,255,0.95)',
        font_color='#000',
        bordercolor='rgba(123, 130, 203, 0.5)'  # Borde con el color #7b82cb
    ),
    margin=dict(l=60, r=40, t=50, b=50),
)

# 🧠 Diccionario global
graph_styles_dict = {
    "classic": graph_style_classic,
    "dark": graph_style_dark,
    "professional": graph_style_professional,
    "gradient": graph_style_gradient,
    "terminal": graph_style_terminal,
    "glass": graph_style_glass,
    "glass1": graph_style_glass1,
    "minimal": graph_style_minimal,
    "alert": graph_style_alert,
    "scientific": graph_style_scientific,
    "compact": graph_style_compact,
}
