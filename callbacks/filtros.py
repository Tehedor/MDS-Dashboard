from dash.dependencies import Input, Output, State
from dash import no_update, ctx

def registrar_callbacks_filtros(app, config, opciones_checklist):
    @app.callback(
        Output('checklist-columnas', 'options'),
        Output('dropdown-componentes', 'value'),
        Output('dropdown-tipo', 'value'),
        [
            Input('dropdown-componentes', 'value'),
            Input('dropdown-tipo', 'value'),
            Input('boton-mostrar-seleccionados', 'n_clicks')
        ],
        State('checklist-columnas', 'options'),
        State('checklist-columnas', 'value'),
        prevent_initial_call=True
    )
    def actualizar_checklist(componente_sel, tipo_sel, n_clicks, opciones_actuales, seleccionados):
        """
        Maneja los filtros de manera independiente y el botón de 'mostrar seleccionados'.
        """
        triggered = ctx.triggered_id  # Qué disparó el callback

        # 🟦 Si se pulsó el botón 'Mostrar seleccionados'
        if triggered == 'boton-mostrar-seleccionados':
            if not seleccionados:
                return no_update, no_update, no_update
            opciones_filtradas = [
                opt for opt in opciones_actuales if opt['value'] in seleccionados
            ]
            return opciones_filtradas, no_update, no_update

        # 🟩 Si se seleccionó un componente → ignorar tipo (lo reseteamos a ALL)
        if triggered == 'dropdown-componentes' and componente_sel not in (None, 'ALL'):
            if componente_sel in config['components']:
                component_data = config['components'][componente_sel]
                measurements = list(component_data['measurements'].keys())
                opciones_filtradas = [
                    opt for opt in opciones_checklist if opt['value'] in measurements
                ]
                return opciones_filtradas, componente_sel, 'ALL'

        # 🟧 Si se seleccionó un tipo → ignorar componente (lo reseteamos a ALL)
        if triggered == 'dropdown-tipo' and tipo_sel not in (None, 'ALL'):
            columnas_tipo = []
            for comp_data in config['components'].values():
                for m_name, m_info in comp_data['measurements'].items():
                    if m_info.get('type', None) == tipo_sel:
                        columnas_tipo.append(m_name)
            opciones_filtradas = [
                opt for opt in opciones_checklist if opt['value'] in columnas_tipo
            ]
            return opciones_filtradas, 'ALL', tipo_sel

        # 🔄 Si ambos están en "ALL" o se limpió todo → mostrar todo
        return opciones_checklist, 'ALL', 'ALL'
