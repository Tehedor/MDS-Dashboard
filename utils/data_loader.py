# ...existing code...
import logging
from math import log
from os import pipe
from pathlib import Path
import pandas as pd


from utils.clean_functions._0_merge_datasets import merge_all_datasets
from utils.clean_functions._1_load_and_process_data import load_and_process_data
from utils.clean_functions._2_clean_and_unify_duplicatses import clean_and_unify_duplicates
from utils.clean_functions._3_negative_frec import negative_freq_report
from utils.clean_functions._4_missing_data import rellenar_timestamps
from utils.clean_functions._5_nomalizar_timestamps import normalize_timestamp_column


# ...existing code...

def _available_functions_map(pipeline: dict) -> dict:
    """Normaliza available_functions en {name: cfg}"""
    out = {}
    if not pipeline:
        return out
    avail = pipeline.get("available_functions", [])
    if isinstance(avail, dict):
        for k, v in avail.items():
            out[k] = v or {}
    elif isinstance(avail, list):
        for item in avail:
            if isinstance(item, dict) and len(item) == 1:
                name, cfg = next(iter(item.items()))
                out[name] = cfg or {}
    return out


def cargar_dataset_completo(pattern_csv: str, pipelineCleanData: dict, timestamp_col: str = "Timestamp") -> pd.DataFrame:
    """
    Carga, unifica y limpia todos los datasets CSV siguiendo la pipeline completa.
    Cada paso se ejecuta solo si está presente en pipelineCleanData.available_functions
    y su campo enabled es True. Si falta en la lista, se salta.
    """
    # normalizar lista de ficheros
    if isinstance(pattern_csv, str):
        csv_list = [pattern_csv]
    else:
        csv_list = list(pattern_csv)

    # si pipeline deshabilitada -> carga simple
    if not pipelineCleanData or pipelineCleanData.get("run_enabled", True) is False:
        logging.info("⚠️ Pipeline de limpieza deshabilitada, se carga solo el CSV sin limpiar")
        dfs = [pd.read_csv(p, parse_dates=[timestamp_col]) for p in csv_list]
        df = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]
        return df

    logging.info("🔹 Ejecutando pipeline de limpieza según configuración")
    funcs_map = _available_functions_map(pipelineCleanData)

    df = None
    # Paso 0: merge_all_datasets
    if funcs_map.get("merge_all_datasets", {}).get("enabled", False):
        logging.info("Ejecutando merge_all_datasets")
        df = merge_all_datasets(csv_list, year_filter=None)
        logging.info(f"✔️ [0] merge_all_datasets: {len(df)} filas, {len(df.columns)} columnas")
    else:
        logging.debug("merge_all_datasets no configurado/disabled -> se salta")

    # Paso 1: load_and_process_data
    if funcs_map.get("load_and_process_data", {}).get("enabled", False):
        if df is None:
            # cargar raw si no existe df
            dfs = [pd.read_csv(p, parse_dates=[timestamp_col]) for p in csv_list]
            df = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]
        logging.info("Ejecutando load_and_process_data")
        df = load_and_process_data(df)
        logging.info(f"✔️ [1] load_and_process_data: {len(df)} filas, {len(df.columns)} columnas")
    else:
        logging.debug("load_and_process_data no configurado/disabled -> se salta")

    # Paso 2: clean_and_unify_duplicates
    if funcs_map.get("clean_and_unify_duplicates", {}).get("enabled", False):
        if df is None:
            dfs = [pd.read_csv(p, parse_dates=[timestamp_col]) for p in csv_list]
            df = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]
        logging.info("✔️ [2] Ejecutando clean_and_unify_duplicates")
        df = clean_and_unify_duplicates(df, "MergedDataset")
    else:
        logging.debug("clean_and_unify_duplicates no configurado/disabled -> se salta")

    # Paso 3: negative_freq_report
    if funcs_map.get("negative_freq_report", {}).get("enabled", False):
        if df is None:
            dfs = [pd.read_csv(p, parse_dates=[timestamp_col]) for p in csv_list]
            df = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]
        logging.info("✔️ [3] Ejecutando negative_freq_report")
        df = negative_freq_report(df)
    else:
        logging.debug("negative_freq_report no configurado/disabled -> se salta")

    # Paso 4: rellenar_timestamps
    anomalies = []
    if funcs_map.get("rellenar_timestamps", {}).get("enabled", False):
        if df is None:
            dfs = [pd.read_csv(p, parse_dates=[timestamp_col]) for p in csv_list]
            df = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]
        logging.info("✔️ [4] Ejecutando rellenar_timestamps")
        df, anomalies = rellenar_timestamps(df)
    else:
        logging.debug("rellenar_timestamps no configurado/disabled -> se salta")

    # Paso 5: normalize_timestamp_column
    if funcs_map.get("normalize_timestamp_column", {}).get("enabled", False):
        if df is None:
            dfs = [pd.read_csv(p, parse_dates=[timestamp_col]) for p in csv_list]
            df = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]
        logging.info("✔️ [5] Ejecutando normalize_timestamp_column")
        df = normalize_timestamp_column(df, timestamp_col)
    else:
        logging.debug("normalize_timestamp_column no configurado/disabled -> se salta")

    if df is None:
        raise RuntimeError("La pipeline no generó DataFrame válido.")

    logging.info("✅ Pipeline de carga completada")
    logging.info(f"📈 Tamaño final: {len(df)} filas, {len(df.columns)} columnas")
    logging.info(f"⚠️ Huecos detectados: {len(anomalies)}")

    return df