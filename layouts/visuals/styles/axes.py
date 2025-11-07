# layouts/visuals/styles/axes_styles.py
# ======================================
# 🎨 Catálogo de estilos de ejes (X, Y) para figuras Plotly/Dash.
# Incluye configuraciones de grid, color, rango, formato y diseño.

# 🧱 Estilo base (claro clásico)
def axes_style_classic(x_min=None, x_max=None, slider_style=None):
    return {
        'xaxis': {
            'type': 'date',
            'range': [x_min, x_max] if x_min else None,
            'rangeslider': slider_style or {},
            'showgrid': True,
            'gridcolor': 'rgba(200,200,200,0.4)',
            'zerolinecolor': 'rgba(180,180,180,0.6)',
            'linecolor': 'rgba(100,100,100,0.4)',
            'mirror': True,
            'ticks': 'outside'
        },
        'yaxis': {
            'autorange': True,
            'showgrid': True,
            'gridcolor': 'rgba(220,220,220,0.4)',
            'zerolinecolor': 'rgba(150,150,150,0.5)',
            'linecolor': 'rgba(100,100,100,0.4)',
            'ticks': 'outside'
        }
    }

# 🌑 Estilo oscuro moderno
def axes_style_dark(x_min=None, x_max=None, slider_style=None):
    return {
        'xaxis': {
            'type': 'date',
            'range': [x_min, x_max] if x_min else None,
            'rangeslider': slider_style or {},
            'showgrid': True,
            'gridcolor': 'rgba(255,255,255,0.1)',
            'zerolinecolor': 'rgba(255,255,255,0.3)',
            'linecolor': 'rgba(255,255,255,0.3)',
            'tickcolor': 'rgba(255,255,255,0.4)',
            'ticks': 'outside'
        },
        'yaxis': {
            'autorange': True,
            'showgrid': True,
            'gridcolor': 'rgba(255,255,255,0.1)',
            'zerolinecolor': 'rgba(255,255,255,0.3)',
            'linecolor': 'rgba(255,255,255,0.3)',
            'tickcolor': 'rgba(255,255,255,0.4)',
            'ticks': 'outside'
        }
    }

# 🧊 Estilo profesional azul
def axes_style_professional(x_min=None, x_max=None, slider_style=None):
    return {
        'xaxis': {
            'type': 'date',
            'range': [x_min, x_max] if x_min else None,
            'rangeslider': slider_style or {},
            'showgrid': True,
            'gridcolor': 'rgba(123, 130, 203, 0.3)',
            'zerolinecolor': 'rgba(123, 130, 203, 0.5)',
            'linecolor': 'rgba(123,130,203,0.5)',
            'mirror': True,
            'ticks': 'outside'
        },
        'yaxis': {
            'autorange': True,
            'showgrid': True,
            'gridcolor': 'rgba(123,130,203,0.2)',
            'zerolinecolor': 'rgba(123,130,203,0.4)',
            'linecolor': 'rgba(123,130,203,0.5)',
            'ticks': 'outside'
        }
    }

# 🌈 Estilo con cuadrícula sutil
def axes_style_soft_grid(x_min=None, x_max=None, slider_style=None):
    return {
        'xaxis': {
            'type': 'date',
            'range': [x_min, x_max] if x_min else None,
            'rangeslider': slider_style or {},
            'showgrid': True,
            'gridcolor': 'rgba(180,180,180,0.15)',
            'zeroline': False,
            'showline': False
        },
        'yaxis': {
            'autorange': True,
            'showgrid': True,
            'gridcolor': 'rgba(180,180,180,0.15)',
            'zeroline': False,
            'showline': False
        }
    }

# 🪩 Estilo retro terminal (verde fosforito)
def axes_style_terminal(x_min=None, x_max=None, slider_style=None):
    return {
        'xaxis': {
            'type': 'date',
            'range': [x_min, x_max] if x_min else None,
            'rangeslider': slider_style or {},
            'showgrid': True,
            'gridcolor': 'rgba(0,255,0,0.1)',
            'zerolinecolor': 'rgba(0,255,0,0.4)',
            'tickcolor': 'rgba(0,255,0,0.6)',
            'ticks': 'outside'
        },
        'yaxis': {
            'autorange': True,
            'showgrid': True,
            'gridcolor': 'rgba(0,255,0,0.1)',
            'zerolinecolor': 'rgba(0,255,0,0.4)',
            'tickcolor': 'rgba(0,255,0,0.6)',
            'ticks': 'outside'
        }
    }

# 💎 Estilo "glass" translúcido
def axes_style_glass(x_min=None, x_max=None, slider_style=None):
    return {
        'xaxis': {
            'type': 'date',
            'range': [x_min, x_max] if x_min else None,
            'rangeslider': slider_style or {},
            'showgrid': True,
            'gridcolor': 'rgba(255,255,255,0.3)',
            'zerolinecolor': 'rgba(255,255,255,0.4)',
            'ticks': 'outside'
        },
        'yaxis': {
            'autorange': True,
            'showgrid': True,
            'gridcolor': 'rgba(255,255,255,0.3)',
            'zerolinecolor': 'rgba(255,255,255,0.4)',
            'ticks': 'outside'
        }
    }

# 🧠 Estilo minimalista (sin cuadrícula, foco en los datos)
def axes_style_minimal(x_min=None, x_max=None, slider_style=None):
    return {
        'xaxis': {
            'type': 'date',
            'range': [x_min, x_max] if x_min else None,
            'rangeslider': slider_style or {},
            'showgrid': False,
            'zeroline': False,
            'showline': False
        },
        'yaxis': {
            'autorange': True,
            'showgrid': False,
            'zeroline': False,
            'showline': False
        }
    }

# ⚙️ Estilo científico (cuadrícula precisa y fina)
def axes_style_scientific(x_min=None, x_max=None, slider_style=None):
    return {
        'xaxis': {
            'type': 'date',
            'range': [x_min, x_max] if x_min else None,
            'rangeslider': slider_style or {},
            'showgrid': True,
            'gridcolor': 'rgba(100,100,255,0.15)',
            'zeroline': False,
            'ticks': 'outside',
            'showspikes': True,
            'spikethickness': 1,
            'spikecolor': 'rgba(0,0,150,0.3)'
        },
        'yaxis': {
            'autorange': True,
            'showgrid': True,
            'gridcolor': 'rgba(100,100,255,0.15)',
            'zeroline': False,
            'ticks': 'outside',
            'showspikes': True,
            'spikethickness': 1,
            'spikecolor': 'rgba(0,0,150,0.3)'
        }
    }

# 🧨 Estilo alerta (cuadrícula rojiza)
def axes_style_alert(x_min=None, x_max=None, slider_style=None):
    return {
        'xaxis': {
            'type': 'date',
            'range': [x_min, x_max] if x_min else None,
            'rangeslider': slider_style or {},
            'showgrid': True,
            'gridcolor': 'rgba(255,0,0,0.2)',
            'zerolinecolor': 'rgba(255,0,0,0.4)',
            'ticks': 'outside'
        },
        'yaxis': {
            'autorange': True,
            'showgrid': True,
            'gridcolor': 'rgba(255,0,0,0.2)',
            'zerolinecolor': 'rgba(255,0,0,0.4)',
            'ticks': 'outside'
        }
    }

# 📘 Diccionario global
axes_styles_dict = {
    "classic": axes_style_classic,
    "dark": axes_style_dark,
    "professional": axes_style_professional,
    "soft_grid": axes_style_soft_grid,
    "terminal": axes_style_terminal,
    "glass": axes_style_glass,
    "minimal": axes_style_minimal,
    "scientific": axes_style_scientific,
    "alert": axes_style_alert,
}