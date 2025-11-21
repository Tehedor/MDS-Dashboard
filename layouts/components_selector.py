# /layouts/components_selector.py
from dash import html, dcc

def componentes_selector(config, opciones_checklist, datasets_disponibles):
    """
    Genera la zona de filtros:
    - Selector de componente
    - Selector de tipo (para TabularDataSet utiliza los tipos del YAML;
      para EventEncodedDataSet ofrece raw/from_to como tipos)
    - Botón "Seleccionados"
    - Selector de dataset (4ª columna)
    - Checklist dinámico
    """

    # ---------------------------------------------------------
    # Si config es None → estamos en carga inicial del layout
    # ---------------------------------------------------------
    if config is None:
        componentes_opts = [{'label': 'Todos', 'value': 'ALL'}]
        tipos_opts = [{'label': 'Todos', 'value': 'ALL'}]
    else:
        # Dropdown de componentes
        componentes_opts = [{'label': 'Todos', 'value': 'ALL'}] + [
            {'label': comp_data.get('name', comp_id), 'value': comp_id}
            for comp_id, comp_data in config.get('components', {}).items()
            if comp_id.lower() != 'timestamp'
        ]

        # Dropdown de tipos
        tipos_unicos = set()
        # Para TabularDataSet: recoger tipos de measurement meta
        for comp_data in config.get('components', {}).values():
            for m_info in comp_data.get("measurements", {}).values():
                tipo = m_info.get("type")
                if tipo and tipo not in ['tiempo', 'time', 'timestamp']:
                    tipos_unicos.add(tipo)

        tipos_opts = [{'label': 'Todos', 'value': 'ALL'}] + [
            {'label': t.capitalize(), 'value': t} for t in sorted(tipos_unicos)
        ]

    # ---------------------------------------------------------
    # Controles
    # ---------------------------------------------------------
    dropdown_componentes = dcc.Dropdown(
        id="dropdown-componentes",
        options=componentes_opts,
        value="ALL",
        clearable=False,
    )

    dropdown_tipo = dcc.Dropdown(
        id="dropdown-tipo",
        options=tipos_opts,
        value="ALL",
        clearable=False,
    )

    boton_seleccionados = html.Button(
        "Seleccionados",
        id="boton-mostrar-seleccionados",
        n_clicks=0,
        className=""
    )

    dropdown_dataset = dcc.Dropdown(
        id="dataset-selector",
        options=[{"label": k, "value": k} for k in datasets_disponibles.keys()],
        value=list(datasets_disponibles.keys())[0],
        clearable=False,
    )

    # ---------------------------------------------------------
    # CHECKLIST (vacío inicialmente)
    # ---------------------------------------------------------
    checklist = dcc.Checklist(
        id="checklist-columnas",
        options=opciones_checklist or [],
        value=[],
        inputStyle={"marginRight": "8px"},
        labelStyle={"display": "inline-block", "marginBottom": "6px"},
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fit, minmax(300px, 1fr))",
            "gap": "5px",
            "height": "140px",
            "overflowY": "auto",
            "padding": "10px",
        }
    )

    # ---------------------------------------------------------
    # Layout visual: 4 columnas en la fila superior
    # ---------------------------------------------------------
    return html.Div(
        [
            html.Div(
                className="filtros-container",
                style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr 1fr", "gap": "15px"},
                children=[
                    html.Div([
                        html.Label("Componente:", style={"fontWeight": "bold"}),
                        dropdown_componentes,
                    ]),
                    html.Div([
                        html.Label("Tipo:", style={"fontWeight": "bold"}),
                        dropdown_tipo,
                    ]),
                    html.Div([
                        html.Label(" ", style={"fontWeight": "bold"}), # alineación
                        boton_seleccionados,
                    ]),
                    html.Div([
                        html.Label("Dataset:", style={"fontWeight": "bold"}),
                        dropdown_dataset,
                    ]),
                ],
            ),

            html.Br(),

            html.Div(
                id="zona-checklist",
                children=[
                    html.Label("Selecciona medidas:", style={"fontWeight": "bold"}),
                    checklist,
                ],
            ),
        ]
    )
