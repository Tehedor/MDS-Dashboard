from dash import html, dcc
from layouts.components_selector import componentes_selector

def serve_layout(config, opciones_checklist, columnas_disponibles, x_timer):
    """Crea el layout principal del dashboard."""
    return html.Div(
        style={
            'fontFamily': 'Arial, sans-serif',
            'padding': '20px',
        },
        children=[
            # html.H1('Dashboard Interactivo de Microgrid'),
            html.Hr(),
            
            # Usar el selector de componentes
            componentes_selector(config, opciones_checklist),
            
            html.Hr(),
            
            # Gráfica
            html.Div(
                id='zona-grafico',
                children=[
                    dcc.Graph(id='grafico-temporal', figure={}, style={'height': '70vh'})
                ],
            ),
        ],
    )
