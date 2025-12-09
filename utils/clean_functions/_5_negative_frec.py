# utils/clean_functions/_3_negative_freq.py
import logging
import numpy as np

def negative_freq_report(
    subdataset,
    freq_cols=("MG-LV-MSB_Frequency", "Island_mode_MCCB_Frequency"),
    sentinels=-327.679993,
    atol=1e-6,
):
    """
    Reemplaza valores sentinel por NaN en columnas de frecuencia.
    Opera sobre subdataset.df.
    """
    df = subdataset.df

    # normalizar sentinels
    if isinstance(sentinels, (float, int, np.floating, np.integer)):
        sentinels = [float(sentinels)]

    for col in freq_cols:
        if col not in df.columns:
            continue

        series = df[col]
        logging.info(f"[negative_freq_report] Procesando columna '{col}'")

        for sentinel in sentinels:
            mask = np.isclose(series, sentinel, atol=atol, rtol=0)
            count = int(mask.sum())

            if count > 0:
                df.loc[mask, col] = np.nan
                logging.warning(
                    f"[negative_freq_report] {count} valores reemplazados en '{col}' "
                    f"por ser sentinel={sentinel}"
                )

    return df
