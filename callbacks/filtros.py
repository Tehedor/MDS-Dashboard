# callbacks/filtros.py
from dash import ctx
from dash.dependencies import Input, Output, State
from dash import no_update

from utils.helpers import build_checklist_options_from_components

def registrar_callbacks_filtros(app):
    """
    Callbacks que actualizan checklist según dropdowns:
      - dropdown-componentes
      - dropdown-tipo
      - boton-mostrar-seleccionados
    Observa que las options base vienen de current-components / current-columns.
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
        ],
        [
            State('checklist-columnas', 'value'),
            State('current-components', 'data'),
            State('current-columns', 'data'),
            State('boton-mostrar-seleccionados', 'className'),
        ],
        prevent_initial_call=True
    )
    def actualizar_checklist(componente_sel, tipo_sel, n_clicks,
                              seleccionados, components_dict, cols, boton_clase):
        triggered = ctx.triggered_id

        components_dict = components_dict or {}
        cols = cols or []

        # construir opciones base con helper
        opciones_base = build_checklist_options_from_components(components_dict, None, cols)

        # ... ahora replicar la lógica que ya tenías, pero sobre opciones_base ...
        # Si se pulsa el botón, togglear mostrar solo seleccionados
        if triggered == 'boton-mostrar-seleccionados':
            boton_activo = boton_clase == "active-filter"
            if boton_activo:
                return opciones_base, seleccionados or [], 'ALL', "", 'ALL', "", ""
            else:
                if seleccionados:
                    opciones_filtradas = [opt for opt in opciones_base if opt['value'] in seleccionados]
                    return opciones_filtradas, seleccionados, 'ALL', "", 'ALL', "", "active-filter"
                else:
                    return opciones_base, [], 'ALL', "", 'ALL', "", ""

        # Filtrar por componente seleccionado
        if triggered == 'dropdown-componentes':
            if componente_sel in (None, 'ALL'):
                return opciones_base, seleccionados or [], 'ALL', "", 'ALL', "", ""
            # componente_sel viene del YAML; hay que filtrar por prefix comp_id
            opciones_filtradas = [opt for opt in opciones_base if opt['value'].startswith(f"{componente_sel}::") or f"({componente_sel})" in opt['label']]
            return opciones_filtradas, seleccionados or [], componente_sel, "active-filter", 'ALL', "", ""

        # Filtrar por tipo (para TabularDataSet)
        if triggered == 'dropdown-tipo':
            if tipo_sel in (None, 'ALL'):
                return opciones_base, seleccionados or [], 'ALL', "", 'ALL', "", ""
            # tipo_sel se corresponde con campo type en measurement meta.
            # Para simplificar, filtramos labels que contengan el tipo en lowercase (recomendable: indexar)
            opciones_filtradas = [opt for opt in opciones_base if tipo_sel.lower() in opt['label'].lower()]
            return opciones_filtradas, seleccionados or [], 'ALL', "", tipo_sel, "active-filter", ""

        # fallback
        return opciones_base, seleccionados or [], 'ALL', "", 'ALL', "", ""
