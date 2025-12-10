# utils/clean_functions/_1_assign_timestamp.py
import logging
import pandas as pd

def assign_timestamp_index(subdataset):
    """
    Normaliza la columna Timestamp venga en el formato que venga (string, float, epoch).
    Mantiene SIEMPRE la columna 'Timestamp' y además la usa como índice.
    """

    df = subdataset.df
    ts_col = subdataset.metadata.get("timestamp_col", "Timestamp")

    if ts_col not in df.columns:
        raise RuntimeError(
            f"[assign_timestamp_index] Columna timestamp '{ts_col}' no encontrada"
        )

    # ============================================================
    # 1) Detectar si el timestamp es epoch (float/int)
    # ============================================================
    sample = df[ts_col].iloc[0]

    # Caso epoch (float, int o string numérica)
    if isinstance(sample, (float, int)) or (
        isinstance(sample, str) and sample.replace(".", "", 1).isdigit()
    ):
        logging.info("[assign_timestamp_index] Detectado timestamp tipo epoch → convirtiendo…")
        df[ts_col] = pd.to_datetime(df[ts_col], unit="s", errors="coerce")

    else:
        # Caso timestamp normal ISO
        df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")

    # Eliminar filas inválidas
    before = len(df)
    df = df.dropna(subset=[ts_col])
    removed = before - len(df)
    logging.info(f"[assign_timestamp_index] Filas eliminadas por timestamp inválido: {removed}")

    # Ordenar por timestamp
    df = df.sort_values(ts_col)

    # ============================================================
    # 2) Mantener columna Timestamp Y asignar índice
    # ============================================================
    df = df.set_index(ts_col, drop=False)

    logging.info(f"[assign_timestamp_index] Índice aplicado: dtype={df.index.dtype}")

    # Guardar resultado
    subdataset.df = df
    return df
