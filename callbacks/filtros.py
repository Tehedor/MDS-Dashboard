# callbacks/filtros.py
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
            State('checklist-columnas', 'value'),
            State('boton-mostrar-seleccionados', 'className')  # ✅ NUEVO: Estado del botón
        ],
        prevent_initial_call=True
    )
    def actualizar_checklist(componente_sel, tipo_sel, n_clicks, seleccionados, boton_clase):
        triggered = ctx.triggered_id

        # 🟦 BOTÓN "Mostrar seleccionados" - Toggle ON/OFF
        if triggered == 'boton-mostrar-seleccionados':
            # Verificar si el botón ya está activo
            boton_activo = boton_clase == "active-filter"
            
            if boton_activo:
                # ✅ DESACTIVAR: Volver a mostrar todos
                return (
                    opciones_checklist,  # Mostrar todas las opciones
                    seleccionados or [],  # Mantener selecciones
                    'ALL',  # Resetear componente a "Todos"
                    "",     # Sin clase activa
                    'ALL',  # Resetear tipo a "Todos"
                    "",     # Sin clase activa
                    ""      # Desactivar botón
                )
            else:
                # ✅ ACTIVAR: Mostrar solo seleccionados
                if seleccionados and len(seleccionados) > 0:
                    opciones_filtradas = [
                        opt for opt in opciones_checklist if opt['value'] in seleccionados
                    ]
                    return (
                        opciones_filtradas,  # Mostrar solo seleccionados
                        seleccionados,       # Mantener selecciones
                        'ALL',  # Resetear componente a "Todos"
                        "",     # Sin clase activa
                        'ALL',  # Resetear tipo a "Todos"
                        "",     # Sin clase activa
                        "active-filter"  # Activar botón
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