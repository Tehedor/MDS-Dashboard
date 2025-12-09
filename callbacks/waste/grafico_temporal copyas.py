# callbacks/grafico_temporal.py
import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly_resampler import FigureResampler
from layouts.visuals.graph_style import get_graph_layout

def actualizar_grafico(columnas_seleccionadas, relayout_data, df_plot, x_timer, format_label_with_unit, columnas_info, default_n_shown_samples=400):
    # logging.info(f"Callback ejecutado con columnas: {columnas_seleccionadas}") 
    # (Comentamos el log para no saturar la terminal si hay muchos eventos)

    if not columnas_seleccionadas:
        return go.Figure().update_layout(title="Por favor, selecciona al menos una serie.")

    # 1. Recuperar el rango de zoom actual (solo para el layout, NO para filtrar datos)
    x_min, x_max = None, None
    if relayout_data:
        # Plotly a veces devuelve rangos como strings o floats, aseguramos formato
        if 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
            try:
                x_min = relayout_data['xaxis.range[0]']
                x_max = relayout_data['xaxis.range[1]']
            except Exception:
                pass
    
    # 2. Inicializar FigureResampler
    # default_n_shown_samples controla cuántos puntos se envían al navegador.
    # 1000-2000 es fluido. Si pones más, el navegador sufre.
    fig = FigureResampler(go.Figure(), default_n_shown_samples=default_n_shown_samples)

    # 3. Preparar eje X Global (Numpy Array - View, sin copiar memoria si es posible)
    # Asumimos que df_plot[x_timer] ya es datetime.
    x_values = df_plot[x_timer].values 

    y_min_global, y_max_global = None, None

    # 4. Iterar columnas (Usando Numpy puro para velocidad)
    for col in columnas_seleccionadas:
        # Resolver nombre real de la columna si viene con ::
        col_to_use = col
        if "::" in col:
            try:
                _, _, real_col = col.split("::", 2)
                col_to_use = real_col
            except Exception:
                col_to_use = col

        if col_to_use not in df_plot.columns:
            continue

        # Extraer valores (Numpy array)
        y_values = df_plot[col_to_use].values

        # --- LÓGICA DE FILTRADO CON NUMPY (Rápida) ---
        # Identificamos índices, no creamos dataframes nuevos.
        is_anomaly = (y_values == -999999.0)
        is_null = (y_values == 999999.0)
        
        # Máscara para datos válidos (Línea principal)
        # Excluimos anomalías y nulos para que la línea no de saltos feos a cero
        is_valid = ~(is_anomaly | is_null) & (y_values > -999998.0) & (y_values < 999998.0)

        # A. Traza PRINCIPAL (Línea)
        if np.any(is_valid):
            # Calcular min/max para el auto-rango del eje Y
            # (Opcional: puedes quitar esto si te ralentiza, pero suele ser rápido en numpy)
            valid_subset = y_values[is_valid]
            ymin, ymax = np.min(valid_subset), np.max(valid_subset)
            y_min_global = ymin if y_min_global is None else min(y_min_global, ymin)
            y_max_global = ymax if y_max_global is None else max(y_max_global, ymax)

            etiqueta = format_label_with_unit(col)
            
            # ¡IMPORTANTE! Pasamos el array completo filtrado por bool mask.
            # FigureResampler se encarga de recortar según el zoom del cliente.
            fig.add_trace(
                go.Scatter(name=etiqueta, line=dict(width=2)),
                hf_x=x_values[is_valid],
                hf_y=valid_subset
            )

        # Base Y para pintar los marcadores de error (usamos el mínimo global o 0)
        marker_base_y = y_min_global if y_min_global is not None else 0

        # B. Traza ANOMALÍAS (Marcadores Naranjas)
        if np.any(is_anomaly):
            # Truco de eficiencia: Usamos np.full para no crear listas de Python
            count_anom = np.sum(is_anomaly)
            fig.add_trace(
                go.Scatter(
                    mode='markers',
                    marker=dict(color='orange', size=10, symbol='square'),
                    showlegend=False,
                    name=f"{col} (Anomalía)"
                ),
                hf_x=x_values[is_anomaly],
                hf_y=np.full(count_anom, marker_base_y) 
            )

        # C. Traza NULOS (Marcadores Rojos)
        if np.any(is_null):
            count_null = np.sum(is_null)
            fig.add_trace(
                go.Scatter(
                    mode='markers',
                    marker=dict(color='red', size=10, symbol='square'),
                    showlegend=False,
                    name=f"{col} (Nulo)"
                ),
                hf_x=x_values[is_null],
                hf_y=np.full(count_null, marker_base_y)
            )

    # 5. Configurar Layout (Manteniendo el zoom del usuario)
    slider_min, slider_max = df_plot[x_timer].min(), df_plot[x_timer].max()
    
    # Layout base
    layout_cfg = get_graph_layout(x_min, x_max, slider_min, slider_max)
    
    # Forzar el rango del eje X si existe en relayout_data
    # Esto hace que el usuario "sienta" que se filtró, pero en realidad solo hicimos zoom.
    if x_min and x_max:
        layout_cfg['xaxis']['range'] = [x_min, x_max]

    fig.update_layout(layout_cfg)

    return fig