import logging
import pandas as pd
import plotly.graph_objects as go
from plotly_resampler import FigureResampler

def actualizar_grafico(columnas_seleccionadas, relayout_data, df_plot, x_timer, format_label_with_unit, default_n_shown_samples=400):
    """
    Callback para actualizar el gráfico principal de la app Dash.
    - df_plot: DataFrame global ya preprocesado y cacheado
    - x_timer: columna temporal
    - format_label_with_unit: función auxiliar de etiquetas
    """

    logging.info(f"Callback ejecutado con columnas: {columnas_seleccionadas}")

    if not columnas_seleccionadas:
        return go.Figure().update_layout(title="Por favor, selecciona al menos una serie.")

    # Detectar rango visible del zoom
    x_min, x_max = None, None
    if relayout_data:
        if 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
            x_min = pd.to_datetime(relayout_data['xaxis.range[0]'])
            x_max = pd.to_datetime(relayout_data['xaxis.range[1]'])
            logging.info(f"Nuevo rango detectado: {x_min} → {x_max}")

    # Filtrar rango visible
    df_visible = df_plot[(df_plot[x_timer] >= x_min) & (df_plot[x_timer] <= x_max)] if x_min is not None else df_plot

    fig = FigureResampler(go.Figure(), default_n_shown_samples=default_n_shown_samples)

    y_min_global, y_max_global = None, None
    for col in columnas_seleccionadas:
        etiqueta = format_label_with_unit(col)
        serie = df_visible[[x_timer, col]].copy()

        # Separar anomalías y normales
        serie_anomalos = serie[serie[col] == -999999.0]
        serie_validos = serie[serie[col].between(-999998.0, 999998.0)]

        if not serie_validos.empty:
            ymin, ymax = serie_validos[col].min(), serie_validos[col].max()
            y_min_global = ymin if y_min_global is None else min(y_min_global, ymin)
            y_max_global = ymax if y_max_global is None else max(y_max_global, ymax)

        fig.add_trace(
            go.Scatter(name=etiqueta, line=dict(width=1)),
            hf_x=serie_validos[x_timer],
            hf_y=serie_validos[col]
        )

    y_centro = (y_min_global + y_max_global) / 2 if y_min_global is not None else 0

    # Añadir anomalías
    for col in columnas_seleccionadas:
        serie = df_visible[[x_timer, col]]
        serie_anomalos = serie[serie[col] == -999999.0]
        if not serie_anomalos.empty:
            fig.add_trace(
                go.Scatter(
                    x=serie_anomalos[x_timer],
                    y=[y_centro] * len(serie_anomalos),
                    mode='markers',
                    name=f"{col} (Anómalo)",
                    marker=dict(color='orange', size=10, symbol='square'),
                )
            )

    # Marcar huecos
    df_temp = (
        df_visible[[x_timer]]
        .dropna()
        .sort_values(x_timer)
        .reset_index(drop=True)
    )
    df_temp['delta'] = df_temp[x_timer].diff().dt.total_seconds()
    gaps = df_temp[df_temp['delta'] > 10]

    for _, row in gaps.iterrows():
        # Asegurarse de usar datetime nativo (compatibilidad con Plotly)
        inicio_gap = pd.to_datetime(df_temp.loc[row.name - 1, x_timer]).to_pydatetime()
        fin_gap = pd.to_datetime(df_temp.loc[row.name, x_timer]).to_pydatetime()

        try:
            fig.add_vrect(
                x0=inicio_gap,
                x1=fin_gap,
                fillcolor="red",
                opacity=0.25,
                layer="below",
                line_width=0,
                annotation_text="F",
                annotation_position="top left",
            )
        except Exception as e:
            logging.exception(f"Error al añadir vrect para gap {inicio_gap} → {fin_gap}: {e}")

    # Rango global del slider
    slider_min = df_plot[x_timer].min()
    slider_max = df_plot[x_timer].max()

    fig.update_layout(
        title="Evolución temporal (resampleado dinámico)",
        xaxis_title="Fecha y Hora",
        yaxis_title="Valor",
        hovermode='x unified',
        xaxis=dict(
            type='date',
            range=[x_min, x_max] if x_min else None,
            rangeslider=dict(visible=True, range=[slider_min, slider_max])
        ),
        yaxis=dict(autorange=True)
    )

    return fig
