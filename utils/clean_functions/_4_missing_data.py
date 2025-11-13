import pandas as pd
import numpy as np

def rellenar_timestamps(df, valor_relleno=999999.0, margen=0.5):
    """
    Detecta huecos en el índice temporal de un DataFrame y los rellena 
    con nuevas filas donde el índice falta, usando un valor constante.

    Parámetros:
    -----------
    df : pd.DataFrame
        DataFrame con índice de tipo DatetimeIndex ordenado.
    valor_relleno : float
        Valor que se colocará en las filas creadas (por defecto 9999999.0)
    margen : float
        Tolerancia en segundos para considerar un hueco (por defecto 0.5)

    Retorna:
    --------
    df_completo : pd.DataFrame
        DataFrame con timestamps faltantes insertados.
    anomalies : pd.DataFrame
        Reporte con huecos detectados (prev_ts, curr_ts, gap_seconds, missing_samples)
    """

    # --- 1) Calcular resolución temporal ---
    resolution = df.index.to_series().diff().mode()[0]
    resolution_seconds = resolution.total_seconds()

    # --- 2) Calcular deltas y detectar huecos ---
    deltas = df.index.to_series().diff().dt.total_seconds().dropna()
    off_mask = (deltas - resolution_seconds).abs() > margen
    gaps_s = deltas[off_mask]

    curr_ts = gaps_s.index
    prev_ts = curr_ts - pd.to_timedelta(gaps_s, unit="s")
    missing = np.maximum(0, np.floor((gaps_s + margen) / resolution_seconds).astype(int) - 1)

    anomalies = pd.DataFrame({
        "prev_ts": prev_ts,
        "curr_ts": curr_ts,
        "gap_seconds": gaps_s.values,
        "missing_samples": missing.values
    }).reset_index(drop=True)

    total_missing = int(missing.sum())

    if total_missing == 0:
        print("✅ No se detectaron huecos en los timestamps.")
        return df.copy(), anomalies

    # --- 3) Crear los nuevos timestamps ---
    new_timestamps = []
    for i, row in anomalies.iterrows():
        for j in range(1, row["missing_samples"] + 1):
            ts_missing = row["prev_ts"] + j * resolution
            new_timestamps.append(ts_missing)

    # --- 4) Crear DataFrame con los valores de relleno ---
    df_missing = pd.DataFrame(valor_relleno, index=new_timestamps, columns=df.columns)

    # --- 5) Unir y reordenar ---
    df_completo = pd.concat([df, df_missing]).sort_index()

    print(f"⚠️ Se detectaron {len(anomalies)} huecos.")
    print(f"🧩 Se insertaron {total_missing} filas nuevas con el valor {valor_relleno}.")

    return df_completo, anomalies
