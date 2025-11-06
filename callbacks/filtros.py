from dash.dependencies import Input, Output, State
from dash import no_update

def registrar_callbacks_filtros(app, config, opciones_checklist):
    @app.callback(
        Output('checklist-columnas', 'options'),
        [Input('dropdown-componentes', 'value'),
         Input('dropdown-tipo', 'value')]
    )
    def filtrar_por_componente_y_tipo(componente_sel, tipo_sel):
        opciones_filtradas = opciones_checklist.copy()

        if componente_sel not in (None, 'ALL'):
            if componente_sel in config['components']:
                component_data = config['components'][componente_sel]
                measurements = list(component_data['measurements'].keys())
                opciones_filtradas = [
                    opt for opt in opciones_filtradas if opt['value'] in measurements
                ]

        if tipo_sel not in (None, 'ALL'):
            columnas_tipo = []
            for comp_data in config['components'].values():
                for m_name, m_info in comp_data['measurements'].items():
                    if m_info.get('type', None) == tipo_sel:
                        columnas_tipo.append(m_name)
            opciones_filtradas = [
                opt for opt in opciones_filtradas if opt['value'] in columnas_tipo
            ]

        return opciones_filtradas

    # 👇 Callback para el botón "Mostrar seleccionados"
    @app.callback(
        Output('boton-mostrar-seleccionados', 'n_clicks'),
        Input('boton-mostrar-seleccionados', 'n_clicks'),
        State('checklist-columnas', 'value')
    )
    def mostrar_seleccionados(n_clicks, seleccionados):
        if n_clicks:
            print("✅ Medidas seleccionadas:", seleccionados)
        return no_update
