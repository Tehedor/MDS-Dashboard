# app.py
import dash
import logging
import os
from pathlib import Path
from dash.dependencies import Input, Output
from dash import html, dcc

from utils.helpers import (
    load_config,
    build_checklist_options_from_components,
)
from utils.dataset_manager import (
    scan_datasets,
    load_processed_or_build,
    get_duckdb_con,
)
from layouts.dashboard_layout import serve_layout
from callbacks.filtros import registrar_callbacks_filtros
from callbacks.grafico_temporal import actualizar_grafico
import shutil
import subprocess

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
log = logging.getLogger("App")

# -------------------------------------------------------------
# Inicialización base
# -------------------------------------------------------------
app = dash.Dash(__name__)
server = app.server

BASE_DATASETS_DIR = Path(__file__).parent / "Datasets"

# -------------------------------------------------------------
# Escanear datasets disponibles
# -------------------------------------------------------------
datasets_disponibles = scan_datasets(BASE_DATASETS_DIR)
logging.info("Datasets disponibles: %s", list(datasets_disponibles.keys()))

if not datasets_disponibles:
    raise RuntimeError("❌ No hay datasets disponibles en /Datasets/*")

# Dataset por defecto = el primero
dataset_actual = list(datasets_disponibles.keys())[0]

# --- Cargar solo el config del dataset seleccionado ---
config_actual = load_config(datasets_disponibles[dataset_actual]["config"])
logging.info("config_actual: %s", datasets_disponibles[dataset_actual])

# ---  Generar pipeline dinámicamente ---
# duckdb_path = datasets_disponibles[dataset_actual]["duckdb"]
# con = get_duckdb_con(duckdb_path)

# logging.info("conectado a DuckDB en %s", duckdb_path)

# df_info, columnas_disponibles = load_processed_or_build(
#     con,
#     datasets_disponibles[dataset_actual],
#     config_actual
# )

# -------------------------------------------------------------
# Layout con dcc.Store y placeholders
# -------------------------------------------------------------
def get_layout():
    return html.Div(
        [
            dcc.Store(id="current-config"),
            dcc.Store(id="current-components"),
            dcc.Store(id="current-columns"),

            serve_layout(
                config=None,               # ya no se usa directamente aquí
                datasets=datasets_disponibles,
                opciones_checklist=[],     # checklist se llenará dinámicamente
                columnas=[],
                x_timer="Timestamp",
            )
        ]
    )

app.layout = get_layout


# -------------------------------------------------------------
# CALLBACK: Cambio de dataset
# -------------------------------------------------------------
@app.callback(
    [
        Output("current-config", "data"),
        Output("current-components", "data"),
        Output("current-columns", "data"),
        Output("checklist-columnas", "options"),
        Output("checklist-columnas", "value"),
    ],
    Input("dataset-selector", "value"),
)
def actualizar_dataset(dataset_name):
    """
    El usuario selecciona un dataset → cargamos configuración, pipeline (si necesario),
    tabla en duckdb y generamos checklist dinámico.
    """
    info = datasets_disponibles[dataset_name]

    # Cargar config.yml del dataset
    cfg = load_config(info["config"])
    components_dict = info.get("components_dict", {}) or {}

    # Conectar a DuckDB y garantizar tabla
    con = get_duckdb_con(info["duckdb"])
    df_sample, cols = load_processed_or_build(con, info, cfg)

    # Generar opciones dinámicas del checklist
    dataset_type = info["type"]
    opciones = build_checklist_options_from_components(
        components_dict,
        dataset_type,
        cols
    )

    # Valor por defecto
    default_value = [opciones[0]["value"]] if opciones else []

    log.info(f"Dataset '{dataset_name}' actualizado: {len(cols)} columnas detectadas")

    return cfg, components_dict, cols, opciones, default_value


# -------------------------------------------------------------
# CALLBACK: Crear gráfico temporal
# -------------------------------------------------------------
@app.callback(
    Output("grafico-temporal", "figure"),
    [
        Input("checklist-columnas", "value"),
        Input("dataset-selector", "value"),
    ]
)
def actualizar_grafico_callback(columnas, dataset_name):
    if not columnas:
        from plotly.graph_objects import Figure
        return Figure().update_layout(title="Selecciona una columna")

    info = datasets_disponibles[dataset_name]

    con = get_duckdb_con(info["duckdb"])

    # Cargar toda la tabla del dataset elegido
    df = con.execute(f"SELECT * FROM {info['table_name']}").df()

    return actualizar_grafico(
        columnas_seleccionadas=columnas,
        relayout_data=None,
        df_plot=df,
        x_timer="Timestamp",
        format_label_with_unit=lambda c: c,   # puedes mejorar más tarde
    )


# -------------------------------------------------------------
# MAIN
# -------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=8050)