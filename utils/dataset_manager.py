import os
import logging
from pathlib import Path
import duckdb
import pandas as pd
import yaml

from utils.helpers import load_config
from utils.data_loader import cargar_dataset_completo

logger = logging.getLogger(__name__)

# -----------------------------------------------------------
# RAM cache global
# -----------------------------------------------------------
RAM_DATASETS: dict[str, pd.DataFrame] = {}

# -----------------------------------------------------------
# ESCANEAR DATASETS
# -----------------------------------------------------------
def scan_datasets(base_dir: Path):
    datasets = {}
    logging.info("🔍 Escaneando datasets en %s", base_dir)

    for ds_dir in sorted(base_dir.iterdir()):
        logging.info("Revisando %s", ds_dir)

        if not ds_dir.is_dir():
            continue

        if ds_dir.name.startswith("."):
            continue

        config_file = ds_dir / "control_dataset.yml"
        if not config_file.exists():
            logging.warning("Dataset %s no tiene control_dataset.yml", ds_dir)
            continue

        # cargar YAML
        with open(config_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        components_file = ds_dir / cfg.get("metadata", {}).get("components", "")
        if components_file.exists():
            with open(components_file, "r", encoding="utf-8") as cf:
                comp_raw = yaml.safe_load(cf) or {}
                components = comp_raw.get("components", comp_raw)
        else:
            components = {}

        processed_dir = ds_dir / "processed"
        processed_dir.mkdir(exist_ok=True)

        duckdb_path = processed_dir / f"{ds_dir.name}.duckdb"

        datasets[ds_dir.name] = {
            "path": ds_dir,
            "config": config_file,
            "components": components,
            "duckdb": duckdb_path,
            "type": cfg["metadata"].get("type", "TabularDataSet"),
            "table_name": ds_dir.name.replace("-", "_").lower(),
            "pipelineCleanData": cfg.get("pipelineCleanData", {}),
        }

    return datasets


# -----------------------------------------------------------
# Conexión DuckDB
# -----------------------------------------------------------
def get_duckdb_con(path: Path):
    path.parent.mkdir(exist_ok=True, parents=True)
    return duckdb.connect(str(path))


# -----------------------------------------------------------
# PIPELINE REAL → cargar_dataset_completo
# -----------------------------------------------------------
def load_processed_or_build(con, dataset_info: dict, config: dict):
    """
    Si DuckDB ya tiene la tabla → usarla.
    Si no → ejecutar tu pipeline REAL y guardarla.
    """
    table = dataset_info["table_name"]
    duckdb_path = dataset_info["duckdb"]
    raw_dir = dataset_info["path"] / "raw"

    logging.info("################################################")
    logging.info("Cargando o generando dataset %s", table)
    logging.info("DuckDB path: %s", duckdb_path)
    logging.info("Raw dir: %s", raw_dir)
    logging.info("################################################")

    # 1) comprobar si tabla existe
    try:
        existing = con.execute("SHOW TABLES").fetchall()
        if (table,) in existing:
            df_sample = con.execute(f"SELECT * FROM {table} LIMIT 5").df()
            cols = [c for c in df_sample.columns if c != "Timestamp"]
            return df_sample, cols
    except Exception:
        pass

    # 2) pipeline REAL
    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        raise RuntimeError(f"No hay CSVs en {raw_dir}")

    df = cargar_dataset_completo(
        [str(f) for f in csv_files],
        pipelineCleanData=config.get("pipelineCleanData", {}),
        timestamp_col="Timestamp"
    )

    if df is None or df.empty:
        raise RuntimeError("Pipeline devolvió vacío")

    # 3) guardar en DuckDB
    con.execute(f"DROP TABLE IF EXISTS {table}")
    con.register("tmp_df", df)
    con.execute(f"CREATE TABLE {table} AS SELECT * FROM tmp_df")
    con.unregister("tmp_df")

    df_sample = df.head(5)
    cols = [c for c in df.columns if c != "Timestamp"]
    return df_sample, cols


# -----------------------------------------------------------
# RAM load
# -----------------------------------------------------------
def load_full_df_to_ram(dataset_name: str, dataset_info: dict):
    logging.info("Loading DF to RAM: %s", dataset_name)
    con = get_duckdb_con(dataset_info["duckdb"])
    table = dataset_info["table_name"]

    df = con.execute(f"SELECT * FROM {table}").df()
    RAM_DATASETS[dataset_name] = df
    return df


def get_ram_df(dataset_name: str):
    return RAM_DATASETS.get(dataset_name)
