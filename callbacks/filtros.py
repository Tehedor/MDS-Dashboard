# callbacks/filtros.py
from dash import ctx
from dash.dependencies import Input, Output, State
from utils.helpers import build_checklist_options


def registrar_callbacks_filtros(app):

    @app.callback(
        [
            # Checklist
            Output("checklist-columnas", "options"),
            Output("checklist-columnas", "value"),

            # Dropdown componentes
            Output("dropdown-componentes", "options"),
            Output("dropdown-componentes", "value"),
            Output("dropdown-componentes", "className"),

            # Dropdown tipos
            Output("dropdown-tipo", "options"),
            Output("dropdown-tipo", "value"),
            Output("dropdown-tipo", "className"),

            # Botón seleccionados
            Output("boton-mostrar-seleccionados", "className"),
        ],
        [
            Input("current-components", "data"),
            Input("current-columns", "data"),
            Input("dataset-selector", "value"),
            Input("dropdown-componentes", "value"),
            Input("dropdown-tipo", "value"),
            Input("boton-mostrar-seleccionados", "n_clicks"),
        ],
        [
            State("checklist-columnas", "value"),
        ],
        prevent_initial_call=False
    )
    def actualizar(
        components_meta,
        cols_all,
        dataset,
        componente_sel,
        tipo_sel,
        n_clicks,
        seleccionados,
    ):
        trigger = ctx.triggered_id

        # --------------------------------------------------
        # SIN COLUMNAS → TODO VACÍO
        # --------------------------------------------------
        if not cols_all:
            return [], [], [], "ALL", "", [], "ALL", "", ""

        # --------------------------------------------------
        # RESET EXCLUSIVO SEGÚN QUIÉN DISPARA
        # --------------------------------------------------
        if trigger == "dropdown-componentes":
            tipo_sel = "ALL"
            n_clicks = 0

        elif trigger == "dropdown-tipo":
            componente_sel = "ALL"
            n_clicks = 0

        elif trigger == "boton-mostrar-seleccionados":
            componente_sel = "ALL"
            tipo_sel = "ALL"

        # --------------------------------------------------
        # OPCIONES BASE (CHECKLIST COMPLETO)
        # --------------------------------------------------
        opciones = build_checklist_options(cols_all)

        # --------------------------------------------------
        # FILTRO POR COMPONENTE (EXCLUSIVO)
        # --------------------------------------------------
        if componente_sel and componente_sel != "ALL":
            opciones = [
                op for op in opciones
                if op["meta"]["component"] == componente_sel
            ]

        # --------------------------------------------------
        # FILTRO POR TIPO (EXCLUSIVO)
        # --------------------------------------------------
        elif tipo_sel and tipo_sel != "ALL":
            opciones = [
                op for op in opciones
                if op["meta"]["type"] == tipo_sel
            ]

        # --------------------------------------------------
        # FILTRO "SELECCIONADOS" (EXCLUSIVO)
        # --------------------------------------------------
        elif n_clicks and n_clicks % 2 == 1:
            opciones = [
                op for op in opciones
                if op["value"] in (seleccionados or [])
            ]

        # --------------------------------------------------
        # VALORES SELECCIONADOS
        # --------------------------------------------------
        if seleccionados:
            seleccionados = [
                v for v in seleccionados
                if any(op["value"] == v for op in opciones)
            ]

        if not seleccionados and opciones:
            seleccionados = [opciones[0]["value"]]

        # --------------------------------------------------
        # DROPDOWN COMPONENTES
        # --------------------------------------------------
        componentes_opts = [{"label": "Todos", "value": "ALL"}]

        if isinstance(components_meta, dict):
            componentes_opts += [
                {
                    "label": comp_data.get("name", comp_id),
                    "value": comp_id
                }
                for comp_id, comp_data in components_meta.items()
            ]

        # --------------------------------------------------
        # DROPDOWN TIPOS
        # --------------------------------------------------
        tipos_unicos = sorted({
            col.get("type")
            for col in cols_all
            if col.get("type")
        })

        tipos_opts = [{"label": "Todos", "value": "ALL"}] + [
            {"label": t.capitalize(), "value": t}
            for t in tipos_unicos
        ]

        # --------------------------------------------------
        # CLASE BOTÓN SELECCIONADOS
        # --------------------------------------------------
        boton_class = "active" if n_clicks and n_clicks % 2 == 1 else ""

        return (
            opciones,
            seleccionados,
            componentes_opts,
            componente_sel or "ALL",
            "",
            tipos_opts,
            tipo_sel or "ALL",
            "",
            boton_class,
        )
