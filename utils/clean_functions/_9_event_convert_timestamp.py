import pandas as pd

def event_convert_timestamp(df, timestamp_col="Timestamp"):
    """
    Convierte Timestamp a datetime64 en datasets event-encoded.
    """
    if timestamp_col not in df.columns:
        raise ValueError(f"❌ No existe columna {timestamp_col} en dataset de eventos")

    df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors="coerce")
    df.dropna(subset=[timestamp_col], inplace=True)

    return df
