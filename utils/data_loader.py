# utils/data_loader.py
import logging
from math import log
from pathlib import Path
import pandas as pd


from utils.clean_functions._0_merge_datasets import merge_all_datasets
from utils.clean_functions._1_load_and_process_data import load_and_process_data
from utils.clean_functions._2_clean_and_unify_duplicatses import clean_and_unify_duplicates
from utils.clean_functions._3_negative_frec import negative_freq_report
from utils.clean_functions._4_missing_data import rellenar_timestamps
from utils.clean_functions._5_nomalizar_timestamps import normalize_timestamp_column

def cargar_dataset_completo(pattern_csv: str, timestamp_col: str = "Timestamp") -> pd.DataFrame:
    """
    Carga, unifica y limpia todos los datasets CSV siguiendo la pipeline completa:
        1. Carga todos los CSV y crea un DataFrame con índice temporal.
        2. Elimina duplicados por timestamp (promediando).
        3. Sustituye frecuencias negativas (sentinels).
        4. Rellena timestamps faltantes con 9999999.0.
    """

    logging.info("🔹 [0] Cargando y unificando datasets...")
    df = merge_all_datasets(pattern_csv, year_filter=None)
    logging.info(f"✔️ Datasets unificados: {len(df)} filas, {len(df.columns)} columnas")

    # logging.info("🔹 [1] Cargando datasets...")
    # df = load_and_process_data(pattern_csv)
    # logging.info(f"✔️ Datos cargados: {len(df)} filas, {len(df.columns)} columnas")

    logging.info("🔹 [2] Unificando duplicados...")
    df = clean_and_unify_duplicates(df, "MergedDataset")

    logging.info("🔹 [3] Corrigiendo frecuencias negativas...")
    df = negative_freq_report(df)

    logging.info("🔹 [4] Rellenando timestamps faltantes...")
    df, anomalies = rellenar_timestamps(df)

    logging.info("🔹 [5] Normalizando columna de timestamps...")
    df = normalize_timestamp_column(df, timestamp_col)

    logging.info("✅ Pipeline de carga completada")
    logging.info(f"📈 Tamaño final: {len(df)} filas, {len(df.columns)} columnas")
    logging.info(f"⚠️ Huecos detectados: {len(anomalies)}")

    return df


# # ...existing code...
# if __name__ == "__main__":
#     import argparse
#     import logging
#     import tempfile
#     import os
#     import sys
#     from pathlib import Path
#     import pandas as pd

#     logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

#     parser = argparse.ArgumentParser(description="Probar cargar_y_formatear_datasets")
#     parser.add_argument("paths", nargs="*", help="Rutas a archivos CSV (opcional). Si no se pasan, se usa DEFAULT_DATASET_PATHS o se crea un ejemplo.")
#     parser.add_argument("--timestamp-col", default="Timestamp", help="Nombre de la columna timestamp")
#     parser.add_argument("--verbose", action="store_true", help="Imprimir información adicional")
#     args = parser.parse_args()

#     PROJECT_ROOT = Path(__file__).resolve().parents[1]

#     # --- HUECO: pega aquí tus data paths RELATIVOS a la raíz del proyecto ---
#     DEFAULT_DATASET_PATHS = [
#         # "MDS-dataset/202205.csv",
#         "MDS-dataset/202302.csv",
#         "MDS-dataset/202303.csv",
#         # "MDS-dataset/202304.csv",
#         # "MDS-dataset/202305.csv",
#         # "MDS-dataset/202306.csv",
#         # "MDS-dataset/202307.csv",
#     ]
#     # ---------------------------------------
#     dataset_dir = PROJECT_ROOT / "MDS-dataset"
#     csv_files = sorted(dataset_dir.glob("202*.csv"))
#     DEFAULT_DATASET_PATHS = [str(Path("MDS-dataset") / f.name) for f in csv_files]

#     # Resolver rutas relativas respecto a PROJECT_ROOT
#     DEFAULT_DATASET_PATHS = [str((PROJECT_ROOT / p).resolve()) for p in DEFAULT_DATASET_PATHS]

#     # Prioridad: CLI > DEFAULT_DATASET_PATHS
#     if args.paths:
#         paths = [p if os.path.isabs(p) else str((PROJECT_ROOT / p).resolve()) for p in args.paths]
#     elif DEFAULT_DATASET_PATHS:
#         paths = DEFAULT_DATASET_PATHS
#         logging.info("Usando DEFAULT_DATASET_PATHS del script (resueltas desde la raíz del proyecto).")
#     else:
#         paths = []

#     # Filtrar rutas inexistentes
#     existing_paths = []
#     for p in paths:
#         if os.path.exists(p):
#             existing_paths.append(p)
#         else:
#             logging.warning(f"Ruta no encontrada (se ignora): {p}")
#     paths = existing_paths

#     # Si no hay paths válidos, salir con error (no crear sample)
#     if not paths:
#         logging.error("No se encontraron datasets válidos. Abortando.")
#         sys.exit(1)

#     # --- Detectar y volcar timestamps inválidos y timestamps con TODOS datos nulos ---
#         # ...existing code...
#         # --- Detectar y volcar timestamps inválidos y timestamps con TODOS datos nulos ---
#     bad_list = []
#     empty_list = []
#     debug_dir = Path(PROJECT_ROOT) / "utils" / "debug"
#     debug_dir.mkdir(parents=True, exist_ok=True)
#     for p in paths:
#         try:
#             df_raw = pd.read_csv(p, dtype=str)
#         except Exception:
#             logging.warning(f"No se pudo leer {p}")
#             continue

#         posibles_col = [c for c in df_raw.columns if c.lower() == args.timestamp_col.lower()]
#         if not posibles_col:
#             logging.warning(f"{p}: no se encontró columna timestamp ({args.timestamp_col})")
#             continue
#         col_raw = posibles_col[0]

#         # limpiar antes de parsear para capturar problemas por encoding/spaces/BOM
#         ts_parsed = pd.to_datetime(
#             df_raw[col_raw].fillna('').astype(str).str.replace('\ufeff', '', regex=False).str.strip(),
#             errors='coerce'
#         )
#         mask_bad_ts = ts_parsed.isna()
#         if mask_bad_ts.any():
#             df_bad = df_raw.loc[mask_bad_ts].copy()
#             df_bad['__source_file'] = p
#             df_bad['__orig_timestamp'] = df_raw.loc[mask_bad_ts, col_raw].values
#             df_bad['__row_index'] = df_raw.loc[mask_bad_ts].index.values
#             bad_list.append(df_bad)

#         # Detectar filas donde TODOS los campos de datos (no timestamp) están vacíos / nulos
#         data_cols = [c for c in df_raw.columns if c != col_raw]
#         if data_cols:
#             # Evitar applymap/replace costoso: procesar por columnas object
#             df_check = df_raw[data_cols].copy()
#             obj_cols = df_check.select_dtypes(include=["object"]).columns
#             for c in obj_cols:
#                 # strip and normalize common null tokens on string columns
#                 s = df_check[c].astype(str).str.strip()
#                 s = s.replace({'': pd.NA, 'nan': pd.NA, 'NaN': pd.NA, 'None': pd.NA})
#                 df_check[c] = s
#             # For non-object columns we leave values as-is; then coerce everything to numeric where possible
#             df_num = df_check.apply(pd.to_numeric, errors='coerce')
#             mask_empty = (~mask_bad_ts) & df_num.isna().all(axis=1)
#             if mask_empty.any():
#                 df_empty = df_raw.loc[mask_empty].copy()
#                 df_empty['__source_file'] = p
#                 df_empty['__parsed_timestamp'] = ts_parsed.loc[mask_empty].values
#                 df_empty['__row_index'] = df_raw.loc[mask_empty].index.values
#                 empty_list.append(df_empty)
    
#     timestamp_suffix = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
#     if bad_list:
#         bad_df = pd.concat(bad_list, ignore_index=True)
#         bad_path = debug_dir / f"bad_timestamps_{timestamp_suffix}.txt"
#         bad_df.to_csv(bad_path, index=False)
#         logging.info(f"Se han volcado {len(bad_df)} filas con timestamp inválido a: {bad_path}")
#     else:
#         logging.info("No se encontraron timestamps inválidos en los CSV proporcionados.")

#     if empty_list:
#         empty_df = pd.concat(empty_list, ignore_index=True)
#         empty_path = debug_dir / f"empty_timestamps_{timestamp_suffix}.txt"
#         empty_df.to_csv(empty_path, index=False)
#         logging.info(f"Se han volcado {len(empty_df)} filas con TODOS los datos nulos a: {empty_path}")
#     else:
#         logging.info("No se encontraron timestamps con TODOS los datos nulos en los CSV proporcionados.")
#     # ...existing code...
#     try:
#         logging.info(f"Cargando archivos: {paths}")
#         df = cargar_y_formatear_datasets(paths, timestamp_col=args.timestamp_col)

#         logging.info("Resultado: head()")
#         print(df.head().to_string(index=False))

#         if args.verbose:
#             logging.info("Info del DataFrame:")
#             df.info()

#         # Comprobación rápida: conteo de marcas 999999.0 por columna (excluye timestamp)
#         cols_check = [c for c in df.columns if c.lower() != args.timestamp_col.lower()]
#         counts = {c: int((df[c] == 999999.0).sum()) for c in cols_check}
#         logging.info(f"Conteo de 999999.0 por columna: {counts}")

#         # Mostrar rango temporal detectado
#         try:
#             ts_col = [c for c in df.columns if c.lower() == args.timestamp_col.lower()][0]
#             logging.info(f"Rango temporal: {df[ts_col].min()} → {df[ts_col].max()}")
#         except Exception:
#             logging.warning("No se pudo determinar rango temporal.")

#     except Exception:
#         logging.exception("Error al ejecutar la prueba del loader:")
#         sys.exit(1)
#     finally:
#         if sample_created:
#             logging.info("Ejemplo creado en tmp; puedes eliminarlo si quieres.")
# # ...existing code...