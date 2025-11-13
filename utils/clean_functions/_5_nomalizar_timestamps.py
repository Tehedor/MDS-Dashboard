# ...existing code...
import logging
import pandas as pd

def normalize_timestamp_column(df: pd.DataFrame, timestamp_col: str = "Timestamp") -> pd.DataFrame:
    """
    Asegura que el DataFrame tenga una columna 'timestamp_col' de tipo datetime.
    - Renombra columnas coincidentes case-insensitive.
    - Si el índice es DatetimeIndex lo convierte en columna (sin dejar 'index').
    - Si existe alguna columna datetime la usa como timestamp.
    - Fuerza conversión a datetime con errors='coerce'.
    Devuelve el DataFrame modificado.
    """
    # buscar columna case-insensitive
    possible_ts = [c for c in df.columns if c.lower() == timestamp_col.lower()]
    if possible_ts:
        if possible_ts[0] != timestamp_col:
            df = df.rename(columns={possible_ts[0]: timestamp_col})
        logging.debug("Timestamp column found in columns and renamed/kept as '%s'.", timestamp_col)
    else:
        # índice datetime -> pasar a columna
        if isinstance(df.index, pd.DatetimeIndex):
            # nombre real que tendrá la columna tras reset_index()
            orig_idx_col = df.index.name if df.index.name is not None else "index"
            df = df.reset_index().rename(columns={orig_idx_col: timestamp_col})
            # Si reset_index creó "index" y ya existe timestamp_col, eliminar "index"
            if "index" in df.columns and timestamp_col in df.columns and "index" != timestamp_col:
                df = df.drop(columns=["index"])
            logging.debug("DatetimeIndex convertido a columna '%s'.", timestamp_col)
        elif df.index.name and df.index.name.lower() == timestamp_col.lower():
            # índice con nombre 'Timestamp' -> reset y renombrar correctamente
            orig_idx_col = df.index.name
            df = df.reset_index().rename(columns={orig_idx_col: timestamp_col})
            logging.debug("Índice con nombre timestamp convertido a columna '%s'.", timestamp_col)
        else:
            # buscar cualquier columna datetime-like
            datetime_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
            if datetime_cols:
                if datetime_cols[0] != timestamp_col:
                    df = df.rename(columns={datetime_cols[0]: timestamp_col})
                logging.debug("Columna datetime '%s' renombrada a '%s'.", datetime_cols[0], timestamp_col)
            else:
                logging.warning("No se encontró ninguna columna/índice datetime para usar como '%s'.", timestamp_col)

    # forzar dtype datetime (coerce)
    try: 
        if timestamp_col in df.columns:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors="coerce")
    except Exception as e:
        logging.error("Error al convertir la columna '%s' a datetime: %s", timestamp_col, e)

    return df
# ...existing code...