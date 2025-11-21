# app.py
import dash
import logging
import os
from pathlib import Path
from dash.dependencies import Input, Output
from dash import html, dcc

from utils.helpers import load_config, build_checklist_options_from_components
from utils.dataset_manager import (
    scan_datasets,
    load_processed_or_build,
    get_duckdb_con,
    load_full_df_to_ram,
    get_ram_df,
)
from layouts.dashboard_layout import serve_layout
from callbacks.filtros import registrar_callbacks_filtros
from callbacks.grafico_temporal import actualizar_grafico

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
log = logging.getLogger("App")

# -------------------------------------------------------------
# Inicialización base
# -------------------------------------------------------------
app = dash.Dash(__name__)
server = app.server

BASE_DATASETS_DIR = Path(__file__).parent / "Datasets"

# -------------------------------------------------------------
# Escanear datasets disponibles UNA VEZ (no en layout)
# -------------------------------------------------------------
datasets_disponibles = scan_datasets(BASE_DATASETS_DIR)
logging.info("Datasets disponibles: %s", list(datasets_disponibles.keys()))

if not datasets_disponibles:
    raise RuntimeError("❌ No hay datasets disponibles en /Datasets/*")

# Dataset por defecto = el primero
dataset_defecto = list(datasets_disponibles.keys())[0]

# Cargar solo config inicial (no construimos DuckDB todavía)
config_inicial = load_config(datasets_disponibles[dataset_defecto]["config"])
logging.info("Config inicial cargada correctamente")

# Registrar callbacks de filtros (usa stores para datos dinámicos)
registrar_callbacks_filtros(app)

# -------------------------------------------------------------
# Layout estático (evaluado una sola vez)
# -------------------------------------------------------------
def get_layout():
    return html.Div(
        [
            dcc.Store(id="current-config"),
            dcc.Store(id="current-components"),
            dcc.Store(id="current-columns"),
            dcc.Store(id="cached-df"),   # DF serializado JSON

            serve_layout(
                config=config_inicial,
                datasets=datasets_disponibles,
                opciones_checklist=[],
                columnas=[],
                x_timer="Timestamp",
            )
        ]
    )

# IMPORTANT: asignar layout evaluado (no la función) para evitar reevaluaciones
app.layout = get_layout()

# -------------------------------------------------------------
# CALLBACK: al cambiar dataset -> asegurar DuckDB, cargar DF a RAM (si falta),
#             y devolver stores (NO checklist options aquí para evitar duplicados)
# -------------------------------------------------------------
@app.callback(
    [
        Output("current-config", "data"),
        Output("current-components", "data"),
        Output("current-columns", "data"),
        Output("cached-df", "data"),
    ],
    Input("dataset-selector", "value"),
)
def actualizar_dataset(dataset_name):
    info = datasets_disponibles[dataset_name]

    # 1) cargar config y componentes
    cfg = load_config(info["config"])
    components_dict = info.get("components", {}) or {}

    # 2) asegurar tabla DuckDB (no cargamos todo aún)
    con = get_duckdb_con(info["duckdb"])
    # load_processed_or_build garantizará que la tabla exista (sin traer a RAM completo)
    df_head, cols = load_processed_or_build(con, info, cfg)

    # 3) cargar en RAM SOLO SI NO ESTÁ (Option B)
    df_ram = get_ram_df(dataset_name)
    if df_ram is None:
        df_ram = load_full_df_to_ram(dataset_name, info)
    else:
        logging.info("Usando dataset desde RAM: %s", dataset_name)

    # 4) serializar DF a JSON para pasar por Store (orient split es eficiente)
    df_json = df_ram.to_json(date_format="iso", orient="split")

    log.info("Dataset '%s' preparado: filas=%s cols=%s", dataset_name, len(df_ram), len(cols))

    # Devuelve stores (NO checklist aquí)
    return cfg, components_dict, cols, df_json

# -------------------------------------------------------------
# CALLBACK: graficar usando DF cacheado (cached-df store)
# -------------------------------------------------------------
@app.callback(
    Output("grafico-temporal", "figure"),
    [
        Input("checklist-columnas", "value"),
        Input("cached-df", "data"),
    ]
)
def grafico_callback(columnas, df_json):
    from plotly.graph_objects import Figure
    import pandas as pd

    if not columnas:
        return Figure().update_layout(title="Selecciona una columna")

    if not df_json:
        return Figure().update_layout(title="Dataset no cargado todavía")

    df = pd.read_json(df_json, orient="split")

    return actualizar_grafico(
        columnas_seleccionadas=columnas,
        relayout_data=None,
        df_plot=df,
        x_timer="Timestamp",
        format_label_with_unit=lambda c: c
    )

# -------------------------------------------------------------
# MAIN
# -------------------------------------------------------------
if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 8050))
    except:
        port = 8050

    logging.info("Iniciando app en puerto %s", port)
    app.run(debug=True, port=port)
