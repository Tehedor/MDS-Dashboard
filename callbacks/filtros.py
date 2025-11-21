# callbacks/filtros.py
from dash import ctx
from dash.dependencies import Input, Output, State
from dash import no_update
from utils.helpers import build_checklist_options_from_components

def registrar_callbacks_filtros(app):
    """
    Callback único que gestiona:
      - dropdown-componentes
      - dropdown-tipo
      - boton-mostrar-seleccionados
      - dataset-selector (para reinicializar al cambiar dataset)
    Este callback produce checklist.options + checklist.value (única fuente), evitando
    outputs duplicados en la app.
    """

    @app.callback(
        [
            Output('checklist-columnas', 'options'),
            Output('checklist-columnas', 'value'),
            Output('dropdown-componentes', 'value'),
            Output('dropdown-componentes', 'className'),
            Output('dropdown-tipo', 'value'),
            Output('dropdown-tipo', 'className'),
            Output('boton-mostrar-seleccionados', 'className'),
        ],
        [
            Input('dropdown-componentes', 'value'),
            Input('dropdown-tipo', 'value'),
            Input('boton-mostrar-seleccionados', 'n_clicks'),
            Input('dataset-selector', 'value'),  # reinicializa al cambiar dataset
        ],
        [
            State('checklist-columnas', 'value'),
            State('current-config', 'data'),
            State('current-components', 'data'),
            State('current-columns', 'data'),
            State('boton-mostrar-seleccionados', 'className'),
        ],
        prevent_initial_call=False
    )
    def actualizar_checklist(componente_sel, tipo_sel, n_clicks, dataset_name,
                              seleccionados, current_config, components_dict, cols, boton_clase):
        """
        - Cuando dataset_name cambia -> debemos re-generar options base y devolver defaults.
        - Cuando dropdowns o botón cambian -> filtrar opciones sobre la base.
        """

        triggered = ctx.triggered_id

        components_dict = components_dict or {}
        cols = cols or []
        current_config = current_config or {}

        # dataset_type viene del config almacenado
        dataset_type = current_config.get("metadata", {}).get("type") if current_config else None

        # Construir options base
        opciones_base = build_checklist_options_from_components(components_dict, dataset_type, cols)

        # Si no hay opciones base -> fallback con columnas reales
        if not opciones_base:
            opciones_base = [{"label": c, "value": c} for c in cols if c.lower() != "timestamp"]

        # ---------- Caso: cambio de dataset (o carga inicial) ----------
        if triggered == 'dataset-selector' or triggered is None:
            # Resetar todo al cambio de dataset
            default_value = [opciones_base[0]["value"]] if opciones_base else []
            return opciones_base, default_value, 'ALL', "", 'ALL', "", ""

        # ---------- Caso: boton "Mostrar seleccionados" ----------
        if triggered == 'boton-mostrar-seleccionados':
            boton_activo = boton_clase == "active-filter"
            if boton_activo:
                # Desactivar: volver a mostrar todas las opciones
                return opciones_base, seleccionados or [], 'ALL', "", 'ALL', "", ""
            else:
                # Activar: mostrar solo las opciones actualmente seleccionadas
                if seleccionados:
                    opciones_filtradas = [opt for opt in opciones_base if opt['value'] in seleccionados]
                    return opciones_filtradas, seleccionados, 'ALL', "", 'ALL', "", "active-filter"
                else:
                    # no hay seleccionados -> no cambiar
                    return opciones_base, [], 'ALL', "", 'ALL', "", ""

        # ---------- Caso: filtro por componente ----------
        if triggered == 'dropdown-componentes':
            if componente_sel in (None, 'ALL'):
                return opciones_base, seleccionados or [], 'ALL', "", 'ALL', "", ""
            # Filtrar por prefijo "comp_id::" o por label que contenga nombre del componente
            opciones_filtradas = [opt for opt in opciones_base if opt['value'].startswith(f"{componente_sel}::") or f"({componente_sel})" in opt['label']]
            return opciones_filtradas, seleccionados or [], componente_sel, "active-filter", 'ALL', "", ""

        # ---------- Caso: filtro por tipo ----------
        if triggered == 'dropdown-tipo':
            if tipo_sel in (None, 'ALL'):
                return opciones_base, seleccionados or [], 'ALL', "", 'ALL', "", ""
            # Filtrar por tipo: buscamos en labels o en metadata del components_dict
            opciones_filtradas = []
            # First attempt: label matching
            for opt in opciones_base:
                if tipo_sel.lower() in opt['label'].lower():
                    opciones_filtradas.append(opt)
            # If nothing found by label, try components_dict meta (tabular)
            if not opciones_filtradas:
                for comp_id, comp in components_dict.items():
                    for meas_key, meas_meta in comp.get("measurements", {}).items():
                        if meas_meta.get("type") == tipo_sel:
                            # find corresponding option(s)
                            for opt in opciones_base:
                                if opt['value'] == meas_key or opt['value'].endswith(f"::{meas_key}"):
                                    opciones_filtradas.append(opt)
            return opciones_filtradas, seleccionados or [], 'ALL', "", tipo_sel, "active-filter", ""

        # fallback
        return opciones_base, seleccionados or [], 'ALL', "", 'ALL', "", ""
