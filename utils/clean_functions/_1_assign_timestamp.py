import logging
import pandas as pd
import numpy as np


def assign_timestamp_index(subdataset):
    """
    Normaliza la columna Timestamp sin importar el formato:
      - epoch en ms (1651363201000)
      - epoch en s (1651363200 o 1651.36321)
      - strings ISO o similares

    Mantiene SIEMPRE la columna 'Timestamp' y además la usa como índice.
    """

    df = subdataset.df
    ts_col = subdataset.metadata.get("timestamp_col", "Timestamp")

    if ts_col not in df.columns:
        raise RuntimeError(
            f"[assign_timestamp_index] Columna timestamp '{ts_col}' no encontrada"
        )

    sample = df[ts_col].iloc[0]

    # ============================================================
    # 1) DETECCIÓN AUTOMÁTICA DEL TIPO DE TIMESTAMP
    # ============================================================

    def is_number(x):
        if isinstance(x, (int, float, np.number)):
            return True
        if isinstance(x, str):
            return x.replace(".", "", 1).isdigit()
        return False

    if is_number(sample):
        numeric = float(sample)

        if numeric > 1e12:
            # ----------------------------------------------------
            # Caso: epoch en milisegundos (V2)
            # ----------------------------------------------------
            logging.info("[assign_timestamp_index] Detectado epoch en MILISEGUNDOS → converting unit='ms'")
            df[ts_col] = pd.to_datetime(df[ts_col], unit="ms", errors="coerce")

        elif numeric > 1e9:
            # ----------------------------------------------------
            # Caso: epoch en segundos enteros grandes
            # ----------------------------------------------------
            logging.info("[assign_timestamp_index] Detectado epoch en SEGUNDOS grandes → converting unit='s'")
            df[ts_col] = pd.to_datetime(df[ts_col], unit="s", errors="coerce")

        else:
            # ----------------------------------------------------
            # Caso: segundos decimales tipo epoch relativo (tu V1)
            # ----------------------------------------------------
            logging.info("[assign_timestamp_index] Detectado epoch en segundos decimales → converting unit='s'")
            df[ts_col] = pd.to_datetime(df[ts_col], unit="s", errors="coerce")

    else:
        # ------------------------------------------------------------
        # Caso: string ISO o formato extraño → confiar en pandas
        # ------------------------------------------------------------
        logging.info("[assign_timestamp_index] Detectado timestamp tipo string/ISO → to_datetime")
        df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")

    # ============================================================
    # 2) LIMPIEZA Y ORDENACIÓN
    # ============================================================

    before = len(df)
    df = df.dropna(subset=[ts_col])
    removed = before - len(df)
    logging.info(f"[assign_timestamp_index] Filas eliminadas por timestamp inválido: {removed}")

    # ------------------------------------------------------------
    # 🔥 SOLUCIÓN CRÍTICA DEL MERGE:
    # Siempre redondear a segundos exactos.
    # ------------------------------------------------------------
    df[ts_col] = df[ts_col].dt.floor("s")

    df = df.sort_values(ts_col)

    # ============================================================
    # 3) Mantener columna Timestamp y asignarlo como índice
    # ============================================================
    df = df.set_index(ts_col, drop=False)

    logging.info(f"[assign_timestamp_index] Índice aplicado correctamente (dtype={df.index.dtype})")

    # ------------------------------------------------------------
    # Guardar resultado
    # ------------------------------------------------------------
    subdataset.df = df
    return df
