import dash
import logging
from pathlib import Path
from dash.dependencies import Input, Output
from plotly_resampler import register_plotly_resampler

from callbacks.grafico_temporal import actualizar_grafico
from callbacks.filtros import registrar_callbacks_filtros
from utils.cache_config import init_cache
from utils.data_loader import cargar_y_formatear_datasets
from utils.helpers import load_config, format_label_with_unit, get_measurement_info
from layouts.dashboard_layout import serve_layout

# --- Configuración base ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
x_timer = "Timestamp"
config = load_config()

# --- Inicialización de la app ---
app = dash.Dash(__name__)
register_plotly_resampler(app)
cache = init_cache(app)
server = app.server

# --- Cargar datos cacheados ---
@cache.memoize()
def get_data():
    dataset_dir = Path(__file__).parent / "MDS-dataset"
    csv_files = sorted(dataset_dir.glob("202*.csv"))

    dataset_paths = [
        # "MDS-dataset/202205.csv",
        "MDS-dataset/202305.csv",
        # "MDS-dataset/202306.csv",
        # "MDS-dataset/202307.csv",
    ]
    # dataset_paths = [str(Path("MDS-dataset") / f.name) for f in csv_files]
    return cargar_y_formatear_datasets(dataset_paths, x_timer)

# --- Variables globales para layout (se inicializan de forma perezosa) ---
_layout_data_initialized = False
columnas_disponibles = []
opciones_checklist = []

def _initialize_layout_data():
    """Inicializa los datos para el layout solo una vez y de forma perezosa."""
    global _layout_data_initialized, columnas_disponibles, opciones_checklist
    
    if _layout_data_initialized:
        return
    
    logging.info("Cargando datos iniciales...")
    df_initial = get_data()
    columnas_disponibles = [c for c in df_initial.columns if c != x_timer]

    # Generar opciones checklist
    opciones_checklist = []
    for col in columnas_disponibles:
        label = format_label_with_unit(config, col)
        info = get_measurement_info(config, col)
        if info:
            opciones_checklist.append({'label': f"{label} ({info['component']})", 'value': col})
        else:
            opciones_checklist.append({'label': col, 'value': col})

    logging.info(f"Cargadas {len(columnas_disponibles)} columnas para el dashboard")
    _layout_data_initialized = True

# --- Layout (perezoso) ---
def get_layout():
    _initialize_layout_data()
    return serve_layout(config, opciones_checklist, columnas_disponibles, x_timer)

app.layout = get_layout

# --- Callbacks ---
registrar_callbacks_filtros(app, config, opciones_checklist)

@app.callback(
    Output('grafico-temporal', 'figure'),
    [
        # Input('selector-columnas', 'value'),
     Input('checklist-columnas', 'value'),
     Input('grafico-temporal', 'relayoutData')]
)
def callback_wrapper(cols, relayout):
    df = get_data()
    return actualizar_grafico(cols, relayout, df, x_timer, lambda col: format_label_with_unit(config, col))

# --- Main ---
if __name__ == "__main__":
    app.run(debug=True, port=8050)
