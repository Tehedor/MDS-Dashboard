import dash
import logging
import gc
from pathlib import Path
from dash.dependencies import Input, Output
from dash import html, dcc
import pandas as pd
import plotly.graph_objects as go

from config_env import settings_env 

from utils.dataset.DatasetRegistry import DatasetRegistry
from generate_control_yml import generate_control_yml
from utils.cache_config import init_cache, cache_config, limpiar_cache
from layouts.dashboard_layout import serve_layout
from callbacks.filtros import registrar_callbacks_filtros
from callbacks.grafico_temporal import actualizar_grafico
from utils.helpers import format_label_with_unit

# -----------------------------------------------------
# CONFIG
# -----------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
log = logging.getLogger("App")

try:
    generate_control_yml()
except Exception as exc:
    log.error(f"❌ Error generando control.yml: {exc}")
    raise

BASE_DATASETS_DIR = Path(settings_env.OUTPUT_CONTROL).parent
registry = DatasetRegistry(BASE_DATASETS_DIR)

datasets_disponibles = registry.list()
DEFAULT_DATASET = registry.default_dataset
ds_default = registry.get_default()
df_default = ds_default.load_for_visualization()

MAPA_DF_preload = {
    "df": df_default,
    "x_timer": ds_default.main.timestamp_col,
    "ds_obj": ds_default
}

app = dash.Dash(__name__)
cache = init_cache(app)
cache_config(cache)
server = app.server

MAPA_DF = {}
MAPA_EVENT_DICT = {}

# -----------------------------------------------------
# LAYOUT
# -----------------------------------------------------
app.layout = html.Div([
    dcc.Store(id="current-config"),
    dcc.Store(id="current-components"), # Contiene el DICCIONARIO de metadatos
    dcc.Store(id="current-columns"),    # Contiene la LISTA de columnas para el checklist
    dcc.Store(id="cached-df"),
    dcc.Store(id="slider-absolute-range"),
    dcc.Store(id="initial-figure-store"),

    serve_layout(
        config={},
        datasets=datasets_disponibles,
        opciones_checklist=[],
        columnas=[],
        x_timer=MAPA_DF_preload["x_timer"],
        default_dataset=DEFAULT_DATASET,
    ),
])

# -----------------------------------------------------
# CALLBACKS
# -----------------------------------------------------

@app.callback(
    [Output("current-config", "data"), Output("current-components", "data"),
     Output("current-columns", "data"), Output("cached-df", "data"),
     Output("slider-absolute-range", "data")],
    Input("dataset-selector", "value")
)
def cargar_dataset(dataset_name):
    global MAPA_DF, MAPA_EVENT_DICT
    log.info(f"➡ Cargando dataset {dataset_name}...")

    MAPA_DF.clear()
    MAPA_EVENT_DICT.clear()

    if dataset_name == DEFAULT_DATASET:
        df = MAPA_DF_preload["df"]
        x_timer = MAPA_DF_preload["x_timer"]
        ds = MAPA_DF_preload["ds_obj"]
    else:
        try: limpiar_cache(cache)
        except: pass
        gc.collect()
        ds = registry.get(dataset_name)
        df = ds.load_for_visualization()
        x_timer = ds.main.timestamp_col

    MAPA_DF["actual"] = df
    MAPA_DF["x_timer"] = x_timer

    if settings_env.EPOCH_MODE and hasattr(ds, 'epoch') and ds.epoch:
        MAPA_EVENT_DICT.update(ds.epoch.event_dictionary)

    # Consolidar metadatos
    components_cfg = ds.main.components.copy() if ds.main.components else {}
    if settings_env.EPOCH_MODE and hasattr(ds, 'epoch') and ds.epoch and ds.epoch.components:
        for cid, cdata in ds.epoch.components.items():
            if cid not in components_cfg: components_cfg[cid] = cdata
            else: components_cfg[cid]["measurements"].update(cdata.get("measurements", {}))

    components_meta = {}
    columns_meta = []
    for comp_id, comp in components_cfg.items():
        components_meta[comp_id] = {"name": comp.get("name", comp_id), "measurements": {}}
        for mname, mdata in comp.get("measurements", {}).items():
            mtype = mdata.get("type", "tabular")
            components_meta[comp_id]["measurements"][mname] = {
                "type": mtype, "unit": mdata.get("unit"), "display_name": mdata.get("display_name", mname)
            }
            if mname in df.columns:
                columns_meta.append({"name": mname, "component": comp_id, "type": mtype})

    slider_range = {"min": df[x_timer].iloc[0], "max": df[x_timer].iloc[-1]}
    return {}, components_meta, columns_meta, "ready", slider_range

@app.callback(
    Output("initial-figure-store", "data"),
    [Input("current-components", "data"), Input("cached-df", "data")],
    prevent_initial_call=True
)
def preparar_figura_inicial(comp_info, df_ready):
    if df_ready != "ready": return {}
    df = MAPA_DF.get("actual")
    xt = MAPA_DF.get("x_timer")
    num_cols = [c for c in df.columns if c != xt and pd.api.types.is_numeric_dtype(df[c])]
    if not num_cols: return {}
    
    fig = actualizar_grafico([num_cols[0]], None, df, xt, format_label_with_unit, comp_info, None, MAPA_EVENT_DICT)
    return fig.to_plotly_json()

@app.callback(
    Output("grafico-temporal", "figure"),
    [Input("checklist-columnas", "value"), 
     Input("initial-figure-store", "data"),
     Input("current-components", "data"), # <--- CORRECCIÓN: Usar componentes (Dict), no columnas (List)
     Input("grafico-temporal", "relayoutData"),
     Input("slider-absolute-range", "data")]
)
def grafico_callback(sel, fig_ini, comp_info, relayout, slider):
    df = MAPA_DF.get("actual")
    xt = MAPA_DF.get("x_timer")
    if df is None or xt is None: return go.Figure()

    if not sel:
        # Lógica modo vacío
        xmin = slider["min"] if slider else None
        xmax = slider["max"] if slider else None
        if relayout and "xaxis.range[0]" in relayout:
            xmin, xmax = relayout["xaxis.range[0]"], relayout["xaxis.range[1]"]
        fig = go.Figure()
        fig.update_layout(xaxis=dict(range=[xmin, xmax]), yaxis=dict(visible=False),
                          annotations=[dict(text="No hay selección", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=22))])
        return fig

    return actualizar_grafico(sel, relayout, df, xt, format_label_with_unit, comp_info, slider, MAPA_EVENT_DICT)

registrar_callbacks_filtros(app)

if __name__ == "__main__":
    app.run(debug=False, port=settings_env.SERVER_PORT)