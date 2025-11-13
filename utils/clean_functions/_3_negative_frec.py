import pandas as pd
import numpy as np
from typing import Iterable, Union

def negative_freq_report(
    df: pd.DataFrame,
    freq_cols: Iterable[str] = ("MG-LV-MSB_Frequency", "Island_mode_MCCB_Frequency"),
    sentinels: Union[Iterable[float], float] = -327.679993,
    atol: float = 1e-6,
) -> pd.DataFrame:
    """
    Reemplaza en df los valores iguales (dentro de atol) a los sentinels por NaN
    en las columnas listadas en freq_cols. Imprime un resumen por columna y
    devuelve el DataFrame modificado.
    """
    # normalizar sentinels a iterable
    if isinstance(sentinels, (float, int, np.floating, np.integer)):
        sent_list = [float(sentinels)]
    else:
        sent_list = list(sentinels)

    for col in freq_cols:
        if col not in df.columns:
            continue

        print(f"Procesando '{col}'... ", end="")
        col_series = df[col]

        for sentinel in sent_list:
            mask = np.isclose(col_series, sentinel, atol=atol, rtol=0)
            n_replaced = int(mask.sum())
            if n_replaced > 0:
                df.loc[mask, col] = np.nan
                print(f"reemplazados {n_replaced} valores = {sentinel}; ", end="")

        print("listo ✅")

    return df