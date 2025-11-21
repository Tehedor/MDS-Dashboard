# /layouts/dashboard_layout.py
from dash import html, dcc
from layouts.components_selector import componentes_selector

def serve_layout(config, datasets, opciones_checklist, columnas, x_timer="Timestamp"):
    """
    Layout principal del dashboard:
      - Selector componentes / tipos / botón / dataset
      - Checklist dinámico
      - Gráfica temporal
    """

    return html.Div(
        style={
            "backgroundColor": "#f7f7f9",
            'fontFamily': 'Arial, sans-serif',
            "minHeight": "100vh",
            "padding": "20px"
        },
        children=[

            # Filtros + checklist
            componentes_selector(
                config=config,
                opciones_checklist=opciones_checklist,
                datasets_disponibles=datasets
            ),

            # Zona de gráfico temporal
            html.Div(
                id='zona-grafico',
                children=[
                    dcc.Graph(
                        id='grafico-temporal',
                        figure={},
                        style={'height': '70vh'}
                    )
                ],
            ),
        ],
    )
