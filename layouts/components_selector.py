from dash import html, dcc

def componentes_selector(config, opciones_checklist, datasets_disponibles, default_dataset):

    # opciones iniciales
    if not config:
        componentes_opts = [{"label": "Todos", "value": "ALL"}]
        tipos_opts = [{"label": "Todos", "value": "ALL"}]
    else:
        componentes_opts = [{"label": "Todos", "value": "ALL"}] + [
            {"label": comp["name"], "value": comp_id}
            for comp_id, comp in config.items()
            if comp_id.lower() != "timestamp"
        ]

        tipos_unicos = set()
        for comp_data in config.values():
            for m in comp_data.get("measurements", {}).values():
                t = m.get("type")
                if t not in (None, "timestamp", "tiempo"):
                    tipos_unicos.add(t)

        tipos_unicos.update(["raw", "from_to"])
        tipos_opts = [{"label": "Todos", "value": "ALL"}] + \
                     [{"label": t.capitalize(), "value": t} for t in sorted(tipos_unicos)]

    return html.Div(
        [
            # FILA DE SELECTORES — tamaño restaurado
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr 1fr 1fr",
                    "gap": "20px",
                    "marginBottom": "15px",     # 🔥 restaurado
                },
                children=[
                    html.Div([
                        html.Label("Componente:", style={"fontWeight": "bold"}),
                        dcc.Dropdown(
                            id="dropdown-componentes",
                            options=componentes_opts,
                            value="ALL",
                            clearable=False,
                        ),
                    ]),

                    html.Div([
                        html.Label("Tipo:", style={"fontWeight": "bold"}),
                        dcc.Dropdown(
                            id="dropdown-tipo",
                            options=tipos_opts,
                            value="ALL",
                            clearable=False,
                        ),
                    ]),

                    html.Div(
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                            "justifyContent": "flex-end",
                            "width": "160px",
                            "minWidth": "160px",
                            "maxWidth": "160px",
                            "boxSizing": "border-box",
                            "paddingLeft": "8px",
                            "paddingRight": "8px",
                        },
                        children=[
                            html.Button(
                                "Seleccionados",
                                id="boton-mostrar-seleccionados",
                                n_clicks=0,
                                className="",
                                style={
                                    "height": "40px",
                                    "width": "100%",
                                    "fontWeight": "bold",
                                }
                            )
                        ]
                    ),


                    html.Div([
                        html.Label("Dataset:", style={"fontWeight": "bold"}),
                        dcc.Dropdown(
                            id="dataset-selector",
                            options=[{"label": x, "value": x} for x in datasets_disponibles],
                            value=default_dataset,
                            clearable=False,
                        ),
                    ]),
                ]
            ),

            # CHECKLIST — misma altura y tamaño que antes
            html.Div(
                id="zona-checklist",
                children=[
                    html.Label("Selecciona medidas:", style={"fontWeight": "bold"}),
                    dcc.Checklist(
                        id="checklist-columnas",
                        options=opciones_checklist or [],
                        value=[],
                        inputStyle={"marginRight": "8px"},
                        labelStyle={"display": "inline-block", "marginBottom": "6px"},
                        style={
                            "display": "grid",
                            "gridTemplateColumns": "repeat(auto-fit, minmax(300px, 1fr))",
                            "gap": "5px",
                            "height": "150px",
                            "overflowY": "auto",
                            "padding": "10px",
                        },
                    ),
                ],
            )
        ]
    )
