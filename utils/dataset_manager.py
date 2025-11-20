# utils/dataset_manager.py

from math import log
import os
import logging
import importlib
from pathlib import Path
import duckdb
import pandas as pd
import shutil
import yaml
from utils.helpers import load_config
from utils.data_loader import cargar_dataset_completo
from utils.control_yml.eventEncoded_groupComponents import group_components_to_yaml_file


logger = logging.getLogger(__name__)


# -----------------------------------------------------------
# ESCANEAR DATASETS
# -----------------------------------------------------------
def scan_datasets(base_dir: Path):
    """
    Escanea todos los directorios dentro de base_dir y detecta datasets.
    Cada dataset debe tener un control_dataset.yml.
    Devuelve un dict con info de cada dataset.
    """
    datasets = {}
    logging.info("🔍 Escaneando datasets en %s", base_dir)
    for ds_dir in sorted(base_dir.iterdir()):
        logging.info("Revisando %s", ds_dir)
        if not ds_dir.is_dir():
            continue

         # Ignorar directorios ocultos (comienzan por '.')
        if ds_dir.name.startswith("."):
            logging.debug("Ignorado directorio oculto: %s", ds_dir)
            continue

        config_file = ds_dir / "control_dataset.yml"
        if not config_file.exists():
            logging.warning("Dataset %s no tiene control_dataset.yml, se ignora", ds_dir)
            continue

        # Cargar config
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Verificar componente obligatorio
        components_file = ds_dir / config.get("metadata", {}).get("components", "")
        if not components_file.exists():
            if config.get("metadata", {}).get("type") == "EventEncodedDataSet":
                # Generar groupedDictionary automáticamente
                data_rel = config.get("metadata", {}).get("dictionary", "")
                if not data_rel:
                    raise FileNotFoundError(f"Dataset {ds_dir} no tiene 'dictionary' en metadata")
                data_path = ds_dir / data_rel
                if not data_path.exists():
                    raise FileNotFoundError(f"Dataset {ds_dir} requiere fichero {data_path}")
                data = str(data_path)
                out_put_file = config.get("metadata", {}).get("components", "control_groupedDictionary.yml")
                if not group_components_to_yaml_file(data, out_put_file):
                    raise FileNotFoundError(f"Dataset {ds_dir} requiere componente {components_file}")
       
        if components_file.exists():
            try:
                with open(components_file, "r", encoding="utf-8") as cf:
                    loaded = yaml.safe_load(cf) or {}
                    components_data = loaded.get("components", loaded)  
            except Exception as e:
                logging.warning("No se pudo leer components YAML %s: %s", components_file, e)
                components_data = {}
        else:
            components_data = {}


        # DuckDB
        processed_dir = ds_dir / "processed"
        processed_dir.mkdir(exist_ok=True)

        duckdb_path = processed_dir / f"{ds_dir.name}.duckdb"



        datasets[ds_dir.name] = {
            "path": ds_dir,
            "config": config_file,
            "components": components_data,
            "duckdb": duckdb_path,
            "type": config["metadata"].get("type", "TabularDataSet"),
            "table_name": ds_dir.name.replace("-", "_").lower(),
            "pipelineCleanData": config.get("pipelineCleanData", {}),
        }

    return datasets


# -----------------------------------------------------------
# CREAR O ABRIR CONEXIÓN A DUCKDB
# -----------------------------------------------------------
def get_duckdb_con(db_path: Path):
    """Conexión a DuckDB (crea DB si no existe)."""
    con = duckdb.connect(database=str(db_path), read_only=False)
    return con

# -----------------------------------------------------------
# EJECUTAR PIPELINE DINÁMICAMENTE
# -----------------------------------------------------------
def run_pipeline(config, dataset_info):
    """
    Ejecuta el pipeline definido en el YAML, cargando módulos dinámicamente.
    Retorna el DataFrame procesado.
    """

    df = None

    steps = config.get("pipelineCleanData", {}).get("available_functions", [])

    for step in steps:
        if not step.get("enabled", False):
            continue

        module_path = step["module"]
        func_name = step["func"]

        module = importlib.import_module(module_path)
        func = getattr(module, func_name)

        logger.info(f"Ejecutando paso: {func_name}")

        df = func(df, dataset_info)

    return df


# -----------------------------------------------------------
# EJECUTAR PIPELINE
# -----------------------------------------------------------


def load_processed_or_build(con: duckdb.DuckDBPyConnection, dataset_info: dict, config: dict) -> tuple[pd.DataFrame, list[str]]:
    """
    Genera DuckDB a partir de CSV si no existe o si hay que regenerar.
    Devuelve df de info inicial y lista de columnas disponibles.
    """

    table_name = dataset_info["table_name"]
    duckdb_path = dataset_info["duckdb"]
    raw_dir = dataset_info["path"] / "raw"
    
    
    logging.info("################################################")
    logging.info("Cargando o generando dataset %s", table_name  )
    logging.info("DuckDB path: %s", duckdb_path)
    logging.info("Raw dir: %s", raw_dir)
    logging.info("################################################")


    # Si DuckDB ya existe y tiene la tabla, solo leer columnas
    try:
        existing_tables = con.execute("SHOW TABLES").fetchall()
        if (table_name,) in existing_tables:
            df_info = con.execute(f"SELECT * FROM {table_name} LIMIT 5").df()
            columnas_disponibles = [c for c in df_info.columns if c != "Timestamp"]
            return df_info, columnas_disponibles
    except Exception as e:
        logging.warning("DuckDB vacía o tabla no encontrada: %s", e)

    # --- Generar dataset limpio ---
    logging.info("🚀 Construyendo dataset %s desde raw", table_name)
    csv_files = sorted(raw_dir.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No se encontraron CSVs en {raw_dir}")

    # Cargar y limpiar
    df = cargar_dataset_completo([
        str(f) for f in csv_files], 
        pipelineCleanData=dataset_info["pipelineCleanData"], 
        timestamp_col="Timestamp")
    if df is None or df.empty:
        raise RuntimeError(f"Pipeline produjo un DataFrame vacío para {dataset_info['path']}")

    # Guardar DuckDB
    con.execute(f"DROP TABLE IF EXISTS {table_name}")
    con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
    logging.info("✔️ Dataset cargado en DuckDB: %s", table_name)

    columnas_disponibles = [c for c in df.columns if c != "Timestamp"]
    df_info = df.head(5)
    return df_info, columnas_disponibles