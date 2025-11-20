# /layouts/dashboard_layout.py
from dash import html, dcc
from layouts.components_selector import componentes_selector

# def serve_layout(config, opciones_checklist, columnas_disponibles, x_timer):
def serve_layout(config, datasets,opciones_checklist, columnas, x_timer="Timestamp"):
    """Crea el layout principal del dashboard."""
    return html.Div(
        style={
            "backgroundColor": "#f7f7f9",
            'fontFamily': 'Arial, sans-serif',
            "minHeight": "100vh",  # Asegura que cubra toda la altura de la ventana
            "padding": "20px"
        },
        children=[
            # html.H1('Dashboard Interactivo de Microgrid'),
            # html.Hr(),
            
            html.Label("Dataset"),
            dcc.Dropdown(
                id="dataset-selector",
                options=[{"label": k, "value": k} for k in datasets.keys()],
                value=list(datasets.keys())[0],
            ),

            # Usar el selector de componentes
            # componentes_selector(config, opciones_checklist),
            
            # html.Hr(),
            html.Div(id="placeholder-dataset-selector"),

            html.Label("Columnas a mostrar"),
            dcc.Checklist(
                id="checklist-columnas",
                options=[{"label": col, "value": col} for col in columnas],
                value=[],
            ),


            # Gráfica
            html.Div(
                id='zona-grafico',
                children=[
                    dcc.Graph(id='grafico-temporal', figure={}, style={'height': '70vh'})
                ],

            ),

            # dcc.Graph(id="grafico-temporal"),


        ],
    )
