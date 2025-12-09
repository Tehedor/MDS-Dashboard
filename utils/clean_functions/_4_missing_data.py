# utils/clean_functions/_4_missing_data.py
import logging
import pandas as pd
import numpy as np

def rellenar_timestamps(subdataset, valor_relleno=999999.0, margen=0.5):
    """
    Rellena huecos temporales generando filas nuevas con un valor fijo.
    Retorna solo el df, pero genera reporte de huecos por logging.
    """
    df = subdataset.df

    if not isinstance(df.index, pd.DatetimeIndex):
        raise RuntimeError("[rellenar_timestamps] El índice debe ser un DatetimeIndex")

    # --- resolución temporal ---
    resolution = df.index.to_series().diff().mode()[0]
    resolution_s = resolution.total_seconds()

    deltas = df.index.to_series().diff().dt.total_seconds().dropna()
    off_mask = (deltas - resolution_s).abs() > margen
    gaps_s = deltas[off_mask]

    curr_ts = gaps_s.index
    prev_ts = curr_ts - pd.to_timedelta(gaps_s, unit="s")
    missing_samples = np.maximum(
        0, np.floor((gaps_s + margen) / resolution_s).astype(int) - 1
    )

    anomalies = pd.DataFrame({
        "prev_ts": prev_ts,
        "curr_ts": curr_ts,
        "gap_seconds": gaps_s.values,
        "missing_samples": missing_samples.values
    })

    total_missing = int(missing_samples.sum())

    if total_missing == 0:
        logging.info("[rellenar_timestamps] No se detectaron huecos en timestamps.")
        return df

    logging.warning(
        f"[rellenar_timestamps] {len(anomalies)} huecos detectados. "
        f"Se insertarán {total_missing} nuevas filas."
    )

    # --- crear timestamps que faltan ---
    new_ts = []
    for idx, row in anomalies.iterrows():
        for j in range(1, row["missing_samples"] + 1):
            new_ts.append(row["prev_ts"] + j * resolution)

    df_missing = pd.DataFrame(
        valor_relleno, index=new_ts, columns=df.columns
    )

    df_full = pd.concat([df, df_missing]).sort_index()

    logging.info(
        f"[rellenar_timestamps] Insertadas {total_missing} filas nuevas con valor={valor_relleno}"
    )

    return df_full
