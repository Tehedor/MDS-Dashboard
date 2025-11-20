# callbacks/grafico_temporal.py
import plotly.graph_objects as go

def actualizar_grafico(columnas_seleccionadas, relayout_data, df_plot, x_timer, format_label_with_unit):
    if not columnas_seleccionadas:
        fig = go.Figure()
        fig.update_layout(title="Selecciona columnas")
        return fig

    fig = go.Figure()

    for col in columnas_seleccionadas:
        fig.add_trace(
            go.Scatter(
                x=df_plot[x_timer],
                y=df_plot[col],
                mode="lines",
                name=format_label_with_unit(col),
            )
        )

    fig.update_layout(
        xaxis=dict(title=x_timer),
        yaxis=dict(title="Valores"),
        height=600,
    )

    return fig
