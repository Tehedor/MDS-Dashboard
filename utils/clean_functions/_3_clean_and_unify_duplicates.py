# utils/clean_functions/_3_clean_and_unify_duplicates.py
import logging
import pandas as pd

def clean_and_unify_duplicates(subdataset):
    """
    Detecta timestamps duplicados y los unifica promediando valores.
    Opera sobre subdataset.df y retorna un df limpio.
    """
    df = subdataset.df

    if not isinstance(df.index, pd.DatetimeIndex):
        raise RuntimeError(
            "[clean_and_unify_duplicates] El índice debe ser DatetimeIndex antes de llamar a esta función"
        )

    duplicated_mask = df.index.duplicated(keep=False)
    duplicated_rows = df[duplicated_mask]

    if len(duplicated_rows) > 0:
        logging.warning(
            f"[clean_and_unify_duplicates] Se encontraron {len(duplicated_rows)} filas con timestamp duplicado."
        )
    else:
        logging.info("[clean_and_unify_duplicates] No hay timestamps duplicados.")

    before = len(df)

    # Unificar duplicados mediante promedio
    df_clean = df.groupby(df.index).mean()

    after = len(df_clean)

    if before != after:
        logging.info(
            f"[clean_and_unify_duplicates] Reducido de {before} → {after} filas tras unificar duplicados."
        )
    else:
        logging.info("[clean_and_unify_duplicates] No se eliminaron filas; índice ya era único.")

    return df_clean
