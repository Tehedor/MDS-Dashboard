# callbacks/filtros.py
from dash import ctx
from dash.dependencies import Input, Output, State
from utils.helpers import build_checklist_options, build_tipo_options, get_tabular_type
from debug.debug import save_debug_info


def registrar_callbacks_filtros(app):

    @app.callback(
        [
            Output("checklist-columnas", "options"),
            Output("checklist-columnas", "value"),

            Output("dropdown-componentes", "options"),
            Output("dropdown-componentes", "value"),
            Output("dropdown-componentes", "className"),

            Output("dropdown-tipo", "options"),
            Output("dropdown-tipo", "value"),
            Output("dropdown-tipo", "className"),

            Output("boton-mostrar-seleccionados", "className"),
        ],
        [
            Input("current-components", "data"),
            Input("current-columns", "data"),

            Input("dropdown-componentes", "value"),
            Input("dropdown-tipo", "value"),
            Input("boton-mostrar-seleccionados", "n_clicks"),
            Input("dataset-selector", "value"),
        ],
        [
            State("checklist-columnas", "value"),
            State("boton-mostrar-seleccionados", "className"),
        ],
        prevent_initial_call=False
    )
    def actualizar(
        components_meta, cols_all,
        comp_sel, tipo_sel, n_clicks, dataset,
        seleccionados, boton_clase
    ):

        trigger = ctx.triggered_id

        # ======================================================
        # 🚨 RESET TOTAL AL CAMBIAR DATASET
        # ======================================================
        if trigger == "dataset-selector":

            if not components_meta or not cols_all:
                return [], [], [], "", "", [], "", "", ""

            opciones_base = build_checklist_options(cols_all)

            componentes_opts = [{'label': 'Todos', 'value': 'ALL'}] + [
                {"label": comp["name"], "value": comp_id}
                for comp_id, comp in components_meta.items()
                if comp_id.lower() != "timestamp"
            ]

            tipos = build_tipo_options(components_meta)
            tipos = [t for t in tipos if t["value"] not in ("tabular", "tiempo")]
            tipos.insert(0, {"label": "Todos", "value": "ALL"})

            default_value = [opciones_base[0]["value"]] if opciones_base else []

            return (
                opciones_base, default_value,
                componentes_opts, "ALL", "",
                tipos, "ALL", "",
                ""   # botón NO activo
            )

        # ======================================================
        # 🚀 PRIMERA CARGA DE DATOS REALES
        # ======================================================
        if trigger in ("current-components", "current-columns"):

            if not components_meta or not cols_all:
                return [], [], [], "", "", [], "", "", ""

            opciones_base = build_checklist_options(cols_all)

            componentes_opts = [{'label': 'Todos', 'value': 'ALL'}] + [
                {"label": comp["name"], "value": comp_id}
                for comp_id, comp in components_meta.items()
                if comp_id.lower() != "timestamp"
            ]

            tipos = build_tipo_options(components_meta)
            tipos = [t for t in tipos if t["value"] not in ("tabular", "tiempo")]
            tipos.insert(0, {"label": "Todos", "value": "ALL"})

            default_value = [opciones_base[0]["value"]] if opciones_base else []

            return (
                opciones_base, default_value,
                componentes_opts, "ALL", "",
                tipos, "ALL", "",
                ""
            )

        # ======================================================
        # 🚦 DESDE AQUÍ LÓGICA NORMAL DE FILTROS
        # ======================================================

        opciones_base = build_checklist_options(cols_all)

        componentes_opts = [{'label': 'Todos', 'value': 'ALL'}] + [
            {"label": comp["name"], "value": comp_id}
            for comp_id, comp in components_meta.items()
            if comp_id.lower() != "timestamp"
        ]

        tipos = build_tipo_options(components_meta)
        tipos = [t for t in tipos if t["value"] not in ("tabular", "tiempo")]
        tipos.insert(0, {"label": "Todos", "value": "ALL"})

        # ------------------------------------------------------
        # Botón mostrar seleccionados
        # ------------------------------------------------------
        if trigger == "boton-mostrar-seleccionados":

            active = boton_clase == "active-filter"

            if active:   # apagar
                return (
                    opciones_base, seleccionados or [],
                    componentes_opts, "ALL", "",
                    tipos, "ALL", "",
                    ""
                )

            else:        # encender
                filtradas = [o for o in opciones_base if o["value"] in seleccionados]

                return (
                    filtradas, seleccionados or [],
                    componentes_opts, "ALL", "",
                    tipos, "ALL", "",
                    "active-filter"
                )

        # ------------------------------------------------------
        # Filtro por componente
        # ------------------------------------------------------
        if trigger == "dropdown-componentes" and comp_sel != "ALL":

            filtradas = [
                o for o in opciones_base
                if o.get("meta", {}).get("component") == comp_sel
            ]

            return (
                filtradas, seleccionados or [],
                componentes_opts, comp_sel, "active-filter",
                tipos, "ALL", "",
                boton_clase
            )

        # ------------------------------------------------------
        # Filtro por tipo (raw, from_to)
        # ------------------------------------------------------
        if trigger == "dropdown-tipo" and tipo_sel != "ALL":

            filtradas = []
            for opt in opciones_base:
                meta = opt["meta"]
                tipo = meta.get("type")

                if tipo == "tabular":
                    tipo_real = get_tabular_type(meta, components_meta)
                    if tipo_real == tipo_sel:
                        filtradas.append(opt)

                elif tipo == tipo_sel:
                    filtradas.append(opt)

            return (
                filtradas, seleccionados or [],
                componentes_opts, comp_sel or "ALL", "",
                tipos, tipo_sel, "active-filter",
                boton_clase
            )

        return (
            opciones_base, seleccionados or [],
            componentes_opts, comp_sel or "ALL", "",
            tipos, tipo_sel or "ALL", "",
            boton_clase
        )
