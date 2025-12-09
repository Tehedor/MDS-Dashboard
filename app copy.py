# app.py
import dash
import logging
import os
from pathlib import Path
from dash.dependencies import Input, Output
from dash import html, dcc
import pandas as pd

from utils.dataset.DatasetRegistry import DatasetRegistry
from utils.cache_config import init_cache, cache_config

from layouts.dashboard_layout import serve_layout
from callbacks.filtros import registrar_callbacks_filtros
from callbacks.grafico_temporal import actualizar_grafico
from debug.debug import save_debug_info


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
log = logging.getLogger("App")

# ------------------------------------------------------------------------------
# CARGA DATASETS
# ------------------------------------------------------------------------------
BASE_DATASETS_DIR = Path(__file__).parent / "Datasets"
registry = DatasetRegistry(BASE_DATASETS_DIR)

datasets_disponibles = registry.list()
if not datasets_disponibles:
    raise RuntimeError("❌ No hay datasets disponibles!")


# ------------------------------------------------------------------------------
# APP + CACHE
# ------------------------------------------------------------------------------
app = dash.Dash(__name__)
cache = init_cache(app)
cache_config(cache)
server = app.server

MAPA_DF = {}   # df en memoria

# ============================================================
# DEBUG: extraer headers del primer dataset compuesto
# ============================================================
primer_dataset = datasets_disponibles[0]             # nombre string del dataset
ds_obj = registry.get(primer_dataset)                # objeto DatasetComposite o DatasetBase
columns = ds_obj.get_all_columns()                             # asegurar que se ha procesado

# 0
save_debug_info(
    content_source=columns,
    filename="debug_get_all_columns",
    head="ESTRUCTURA get_all_columns()"
)


# --- 1) Header del dataset compuesto completo ---
save_debug_info(
    content_source=list(ds_obj.df.columns),
    filename="debug_composite_columns",
    head=f"HEADER DEL DATASET COMPUESTO: {primer_dataset}"
)

# --- 2) Header del dataset MAIN ---
if hasattr(ds_obj, "main"):
    save_debug_info(
        content_source=ds_obj.main.df.head(),
        filename="debug_main_columns",
        head=f"HEADER DEL SUBDATASET MAIN: {ds_obj.main.name}"
    )
# --- DEBUG: guardar filas en timestamp concreto ---
ts = "2023-07-31 23:07:11"
try:
    df_all = ds_obj.df.copy()
    # determinar columna timestamp (fallback a "Timestamp")
    ts_col = getattr(ds_obj, "timestamp_col", None) or (ds_obj.main.timestamp_col if hasattr(ds_obj, "main") else "Timestamp")
    if ts_col not in df_all.columns:
        # si no existe la columna, guardar aviso
        save_debug_info(
            content_source=f"No existe la columna '{ts_col}' en el dataframe compuesto.",
            filename=f"debug_at_{ts.replace(' ', '_').replace(':','-')}",
            head=f"BUSCAR TIMESTAMP {ts}"
        )
    else:
        series_ts = pd.to_datetime(df_all[ts_col], errors="coerce")
        target = pd.to_datetime(ts)
        matched = df_all[series_ts == target]
        if matched.empty:
            save_debug_info(
                content_source=f"No hay filas en {ts} (col '{ts_col}').",
                filename=f"debug_at_{ts.replace(' ', '_').replace(':','-')}",
                head=f"BUSCAR TIMESTAMP {ts}"
            )
        else:
            save_debug_info(
                content_source=matched,  # DataFrame -> save_debug_info usará to_string()
                filename=f"debug_at_{ts.replace(' ', '_').replace(':','-')}",
                head=f"FILAS EN {ts} (col '{ts_col}')"
            )
except Exception as e:
    save_debug_info(
        content_source=f"Error al buscar timestamp {ts}: {e}",
        filename=f"debug_at_{ts.replace(' ', '_').replace(':','-')}_error",
        head=f"ERROR BUSCAR TIMESTAMP {ts}"
    )
# ...existing code...


# --- 3) Header del dataset secundario (si existe) ---
if hasattr(ds_obj, "secondary") and ds_obj.secondary:
    for key, sd in ds_obj.secondary.items():
        save_debug_info(
            content_source=sd.df.head(),
            filename=f"debug_secondary_{key}_columns",
            head=f"HEADER DEL SUBDATASET SECUNDARIO '{key}': {sd.name}"
        )

# ------------------------------------------------------------------------------
# LAYOUT
# ------------------------------------------------------------------------------
def get_layout():
    return html.Div([
        dcc.Store(id="current-config"),
        dcc.Store(id="current-components"),
        dcc.Store(id="current-columns"),
        dcc.Store(id="cached-df"),
        dcc.Store(id="slider-absolute-range"),  #  ⬅⬅ NUEVO: rango global del dataset

        serve_layout(
            config={},
            datasets=datasets_disponibles,
            opciones_checklist=[],
            columnas=[],
            x_timer="Timestamp",
            default_dataset=datasets_disponibles[0],
        ),
    ])

app.layout = get_layout


# ------------------------------------------------------------------------------
# CALLBACK: cargar dataset
# ------------------------------------------------------------------------------
@app.callback(
    [
        Output("current-config", "data"),
        Output("current-components", "data"),
        Output("current-columns", "data"),
        Output("cached-df", "data"),
        Output("slider-absolute-range", "data"),  # ⬅⬅ SE AÑADE EL RANGO GLOBAL
    ],
    Input("dataset-selector", "value")
)
def cargar_dataset(dataset_name):
    log.info(f"➡ Cargando dataset {dataset_name}...")

    ds = registry.get(dataset_name)
    cfg = ds.main.config if hasattr(ds, "main") else {}

    cols_info = ds.get_all_columns()
    components_meta = cols_info.get("components_meta", {})
    all_columns = cols_info.get("all", [])

    df = ds.df.copy()
    MAPA_DF["actual"] = df

    slider_range = {
        "min": df["Timestamp"].iloc[0],
        "max": df["Timestamp"].iloc[-1]
    }

    log.info(f" Dataset OK: {len(df)} filas, {len(df.columns)} columnas")

    return cfg, components_meta, all_columns, "ready", slider_range


# ------------------------------------------------------------------------------
# CALLBACK GRÁFICO — recibe relayoutData + slider-absolute-range
# ------------------------------------------------------------------------------
@app.callback(
    Output("grafico-temporal", "figure"),
    [
        Input("checklist-columnas", "value"),
        Input("cached-df", "data"),
        Input("current-columns", "data"),
        Input("grafico-temporal", "relayoutData"),
        Input("slider-absolute-range", "data"),  # ⬅ Rango absoluto FIJO
    ]
)
def grafico_callback(columnas_sel, trigger, columnas_info, relayout_data, slider_data):

    df = MAPA_DF.get("actual")
    if df is None:
        return {}

    return actualizar_grafico(
        columnas_seleccionadas=columnas_sel,
        relayout_data=relayout_data,
        df_plot=df,
        x_timer="Timestamp",
        format_label_with_unit=lambda c: c,
        columnas_info=columnas_info,
        slider_data=slider_data,   # ⬅ SE PASA
    )


# ------------------------------------------------------------------------------
# FILTROS
# ------------------------------------------------------------------------------
registrar_callbacks_filtros(app)


# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    log.info(f"🚀 Iniciando app en puerto {port}")
    app.run(debug=False, port=port)