# utils/dataset/loader.py
import logging
from pathlib import Path
import pandas as pd
import json
from utils.helpers import load_config
from utils.data_loader import cargar_dataset_completo
import logging

def load_or_build_parquet(subdataset):
    """
    subdataset: instancia de SubDataset
    """

    parquet = subdataset.parquet_file
    if parquet.exists():
        logging.info(f"📦-Parquet ya existe para SubDataset '{subdataset.name}': {parquet}")
        return

    logging.info(f"📦-Construyendo parquet para SubDataset '{subdataset.name}'")
    parquet.parent.mkdir(parents=True, exist_ok=True)

    t = subdataset.type

    if t == "tabular":
        _build_tabular(subdataset)
    elif t == "event-encoded":
        _build_event_encoded(subdataset)
    else:
        raise ValueError(f"Tipo de dataset desconocido: {t}")

# -----------------------------------------
def _build_tabular(sd):
    """
    Construye el parquet de un subdataset TABULAR aplicando toda la pipeline
    de limpieza definida en su control_dataset.yml.
    """
    # Obtener lista de CSV raw
    raw_files = list(sd.raw_dir.glob("*.csv"))
    if not raw_files:
        raise RuntimeError(f"No se encontraron CSV en {sd.raw_dir}")

    # Path completo de control_dataset.yml
    control_path = sd.control_path
    config = load_config(control_path)

    pipeline_cfg = config.get("pipelineCleanData", {})
    timestamp_col = sd.timestamp_col

    # Ejecutar la pipeline EXACTA del user
    df_clean = cargar_dataset_completo(
        pattern_csv=[str(f) for f in raw_files],
        pipelineCleanData=pipeline_cfg,
        timestamp_col=timestamp_col,
    )

    # Asegurar columna timestamp presente y tipo datetime
    if timestamp_col not in df_clean.columns:
        raise ValueError(
            f"❌ Después de la pipeline no existe la columna '{timestamp_col}' en {sd.name}"
        )
    df_clean[timestamp_col] = pd.to_datetime(df_clean[timestamp_col], errors="coerce")

    # Reset index si pipeline dejó Timestamp como índice
    if isinstance(df_clean.index, pd.DatetimeIndex):
        df_clean = df_clean.reset_index().rename(columns={"index": timestamp_col})

    # Escribir parquet final
    df_clean.to_parquet(sd.parquet_file, index=False)

    print(f"✔ Parquet generado con pipeline: {sd.parquet_file}   filas={len(df_clean)}")


# -----------------------------------------
def _build_event_encoded(sd):
    raw_files = list(sd.raw_dir.glob("*.csv"))
    if not raw_files:
        raise RuntimeError(f"No CSV en {sd.raw_dir}")

    # cargar pipeline
    config = load_config(sd.control_file)
    pipeline_cfg = config.get("pipelineCleanData", {})
    timestamp_col = sd.timestamp_col

    # ejecutar pipeline completa
    df = cargar_dataset_completo(
        pattern_csv=[str(f) for f in raw_files],
        pipelineCleanData=pipeline_cfg,
        timestamp_col=timestamp_col
    )

    # ------------------------------------------------------
    # ✔ Timestamp SIEMPRE VIENE COMO ÍNDICE tras la pipeline
    # ------------------------------------------------------
    if not isinstance(df.index, pd.DatetimeIndex):
        raise RuntimeError(
            f"❌ Se esperaba DatetimeIndex tras la pipeline en {sd.name}, pero obtuvimos: {type(df.index)}"
        )

    # convertimos índice → columna para guardar correctamente
    df = df.reset_index().rename(columns={"index": timestamp_col})

    # ------------------------------------------------------
    # ✔ La pipeline devuelve una columna llamada "event"
    #    la convertimos a "event_code"
    # ------------------------------------------------------
    if "event" not in df.columns:
        raise RuntimeError(
            f"❌ La pipeline no devolvió columna 'event' en {sd.name}. Columnas={list(df.columns)}"
        )

    df = df.rename(columns={"event": "event_code"})

    # mantener solo las columnas necesarias
    df = df[[timestamp_col, "event_code"]]

    # ------------------------------------------------------
    # ✔ Guardar parquet final
    # ------------------------------------------------------
    df.to_parquet(sd.parquet_file, index=False)
    print(f"✔ Parquet de eventos generado: {sd.parquet_file} | filas={len(df)}")
