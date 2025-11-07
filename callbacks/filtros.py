from dash.dependencies import Input, Output, State
from dash import no_update, ctx

def registrar_callbacks_filtros(app, config, opciones_checklist):
    """Registra los callbacks relacionados con los filtros."""
    
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
            Input('boton-mostrar-seleccionados', 'n_clicks')
        ],
        [
            State('checklist-columnas', 'value')
        ],
        prevent_initial_call=True
    )
    def actualizar_checklist(componente_sel, tipo_sel, n_clicks, seleccionados):
        triggered = ctx.triggered_id

        # 🟦 BOTÓN "Mostrar seleccionados"
        if triggered == 'boton-mostrar-seleccionados':
            # Si ya estaba activo (mostrar solo seleccionados), volver a mostrar todos
            if seleccionados and len(seleccionados) > 0:
                # Alternar entre mostrar seleccionados y mostrar todos
                # Detectar si ya está filtrado comparando opciones actuales vs todas
                opciones_filtradas = [
                    opt for opt in opciones_checklist if opt['value'] in seleccionados
                ]
                valores_validos = [v for v in (seleccionados or []) if v in [o['value'] for o in opciones_filtradas]]
                
                return (
                    opciones_filtradas,
                    valores_validos,
                    'ALL',  # Resetear componente
                    "",     # Sin clase activa
                    'ALL',  # Resetear tipo
                    "",     # Sin clase activa
                    "active-filter"  # Botón activo
                )
            else:
                # No hay seleccionados, no hacer nada
                return (
                    opciones_checklist,
                    [],
                    'ALL',
                    "",
                    'ALL',
                    "",
                    ""
                )

        # 🟩 FILTRO POR COMPONENTE
        if triggered == 'dropdown-componentes':
            if componente_sel in (None, 'ALL'):
                # Resetear: mostrar todas las opciones, mantener selecciones
                return (
                    opciones_checklist,
                    seleccionados or [],  # ✅ Mantener selecciones actuales
                    'ALL',
                    "",
                    'ALL',  # Resetear tipo
                    "",
                    ""      # Resetear botón
                )
            
            # Filtrar por componente específico
            if componente_sel in config['components']:
                component_data = config['components'][componente_sel]
                measurements = list(component_data['measurements'].keys())
                opciones_filtradas = [
                    opt for opt in opciones_checklist if opt['value'] in measurements
                ]
                
                return (
                    opciones_filtradas,
                    seleccionados or [],  # ✅ Mantener selecciones actuales
                    componente_sel,
                    "active-filter",  # Componente activo
                    'ALL',            # Resetear tipo
                    "",
                    ""                # Resetear botón
                )

        # 🟧 FILTRO POR TIPO DE MEDIDA
        if triggered == 'dropdown-tipo':
            if tipo_sel in (None, 'ALL'):
                # Resetear: mostrar todas las opciones, mantener selecciones
                return (
                    opciones_checklist,
                    seleccionados or [],  # ✅ Mantener selecciones actuales
                    'ALL',  # Resetear componente
                    "",
                    'ALL',
                    "",
                    ""      # Resetear botón
                )
            
            # Filtrar por tipo de medida
            columnas_tipo = []
            for comp_data in config['components'].values():
                for m_name, m_info in comp_data['measurements'].items():
                    if m_info.get('type', None) == tipo_sel:
                        columnas_tipo.append(m_name)
            
            opciones_filtradas = [
                opt for opt in opciones_checklist if opt['value'] in columnas_tipo
            ]
            
            return (
                opciones_filtradas,
                seleccionados or [],  # ✅ Mantener selecciones actuales
                'ALL',            # Resetear componente
                "",
                tipo_sel,
                "active-filter",  # Tipo activo
                ""                # Resetear botón
            )

        # 🔁 Fallback: no hacer nada
        return (
            opciones_checklist,
            seleccionados or [],  # ✅ Mantener selecciones actuales
            'ALL',
            "",
            'ALL',
            "",
            ""
        )