from dash import html, dcc

def componentes_selector(config, opciones_checklist):
    """Genera los filtros y el checklist de medidas de forma dinámica y responsive."""

    # --- Dropdown de componentes ---
    opciones_componentes = [
        {'label': 'Todos', 'value': 'ALL'}
    ] + [
        {'label': comp_data.get('name', comp_id), 'value': comp_id}
        for comp_id, comp_data in config['components'].items()
        if comp_id.lower() != 'timestamp'
    ]

    dropdown_componentes = dcc.Dropdown(
        id="dropdown-componentes",
        options=opciones_componentes ,
        value="ALL",
        placeholder="Selecciona un componente",
        clearable=False,
        style={"marginBottom": "10px"}
    )

    # --- Tipos de medida dinámicos ---
    tipos_unicos = set()
    for comp_data in config['components'].values():
        for m_info in comp_data.get("measurements", {}).values():
            tipo = m_info.get("type")
            if tipo and tipo not in ['tiempo', 'time', 'timestamp']:
                tipos_unicos.add(tipo)
    opciones_tipo = [
        {'label': 'Todos', 'value': 'ALL'}
    ] + [
        {'label': tipo.capitalize(), 'value': tipo} for tipo in sorted(tipos_unicos)
    ]

    dropdown_tipo = dcc.Dropdown(
        id="dropdown-tipo",
        options=opciones_tipo,
        value="ALL",
        placeholder="Selecciona un tipo de medida",
        clearable=False,
        style={"marginBottom": "10px"}
    )

    # --- Botón ---
    boton_mostrar = html.Button(
        "Seleccionados",
        id="boton-mostrar-seleccionados",
        n_clicks=0,
        className="btn btn-primary",
        style={
            "padding": "8px 12px",
            "borderRadius": "5px",
            "cursor": "pointer",
            "marginTop": "5px",
        },
    )

    # --- Checklist con estilo tipo grid responsivo ---
    checklist = dcc.Checklist(
        id="checklist-columnas",
        options=opciones_checklist,
        value=[opciones_checklist[0]['value']] if opciones_checklist else [],
        inputStyle={"marginRight": "8px"},
        labelStyle={"display": "inline-block", "marginBottom": "6px"},
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fit, minmax(300px, 1fr))",
            "gap": "5px",
            "height": "140px",
            # "maxHeight": "300px",
            "overflowY": "auto",
            "border": "1px solid #ccc",
            "padding": "10px",
            "borderRadius": "5px",
        },
    )

    # --- Diseño con filtros en línea ---
    layout = html.Div(
        style={"marginBottom": "20px"},
        children=[
            # Filtros en línea
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr auto",
                    "gap": "15px",
                    "alignItems": "end",
                    "marginBottom": "15px"
                },
                children=[
                    html.Div(
                        children=[
                            html.Label("Componente:", style={"fontWeight": "bold", "marginBottom": "5px", "display": "block"}),
                            dropdown_componentes,
                        ],
                    ),
                    html.Div(
                        children=[
                            html.Label("Tipo de medida:", style={"fontWeight": "bold", "marginBottom": "5px", "display": "block"}),
                            dropdown_tipo,
                        ],
                    ),
                    html.Div(
                        children=[boton_mostrar],
                    ),
                ],
            ),
            # Checklist
            html.Div(
                id="zona-checklist",
                children=[
                    html.Label("Selecciona medidas:", style={"fontWeight": "bold", "marginBottom": "8px", "display": "block"}),
                    checklist,
                ],
            ),
        ],
    )

    return layout
