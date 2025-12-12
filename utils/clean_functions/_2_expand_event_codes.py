# utils/clean_functions/_2_expand_event_codes.py
import logging
import pandas as pd
import numpy as np


def expand_event_codes(subdataset):
    """
    Convierte un dataset epoch (Timestamp + event codes) en columnas por medida.

    Ahora configurable mediante EVENT_TYPES para poder aceptar cualquier nombre
    posible de columna que represente códigos de eventos.
    """

    # --------------------------------------------------------------------
    # 0) Definir qué columnas pueden contener códigos de eventos
    # --------------------------------------------------------------------
    EVENT_TYPES = ["event", "event_id", "evt", "code", "codigo_evento"]
    # Si en el futuro quieres añadir otro nombre, basta con meterlo en la lista ↑

    df = subdataset.df
    ctl = subdataset.componentes   # metadata generada automáticamente

    # --------------------------------------------------------------------
    # 1) Detectar columna de eventos según la lista configurable
    # --------------------------------------------------------------------
    event_col = None
    for col in EVENT_TYPES:
        if col in df.columns:
            event_col = col
            break

    if event_col is None:
        raise RuntimeError(
            f"expand_event_codes() → no se encontró ninguna columna de eventos entre: {EVENT_TYPES}"
        )

    logging.info(f"[expand_event_codes] Usando columna de eventos: '{event_col}'")

    # --------------------------------------------------------------------
    # 2) Asegurar timestamp correcto (soporta UNIX float)
    # --------------------------------------------------------------------
    ts_col = subdataset.timestamp_col  # normalmente "Timestamp"

    if ts_col not in df.columns:
        raise RuntimeError(f"expand_event_codes() → falta columna timestamp '{ts_col}'")

    # Caso UNIX float → convertir
    if np.issubdtype(df[ts_col].dtype, np.number):
        logging.warning("Timestamp numérico detectado → convirtiendo desde UNIX epoch...")
        df[ts_col] = pd.to_datetime(df[ts_col], unit="s", errors="coerce")

    # Si no es datetime → convertir igualmente
    if not np.issubdtype(df[ts_col].dtype, np.datetime64):
        logging.warning("Forzando conversión de Timestamp a datetime...")
        df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")

    # Establecer índice
    df = df.set_index(ts_col).sort_index()

    # --------------------------------------------------------------------
    # 3) Construir mapas de códigos desde ctl_components.yml
    # --------------------------------------------------------------------
    raw_map = {}
    ft_map = {}

    for comp, compdata in ctl["components"].items():
        for mname, mdata in compdata["measurements"].items():

            codes = set(mdata["encodes"])
            mtype = mdata["type"]

            if mtype == "event":  # RAW
                raw_map[mname] = codes

            elif mtype == "from_to":  # TRANSICIONES
                ft_map[mname] = codes

    # --------------------------------------------------------------------
    # 4) Agrupación real por timestamp
    # --------------------------------------------------------------------
    grouped = df.groupby(df.index)[event_col].apply(list).reset_index()
    grouped = grouped.rename(columns={event_col: "codes"})

    out = grouped.copy()

    # --------------------------------------------------------------------
    # 5) Expandir columnas RAW
    # --------------------------------------------------------------------
    for name, code_set in raw_map.items():
        out[name] = out["codes"].apply(
            lambda arr: next((c for c in arr if c in code_set), None)
        )

    # --------------------------------------------------------------------
    # 6) Expandir columnas FROM_TO
    # --------------------------------------------------------------------
    for name, code_set in ft_map.items():
        out[name] = out["codes"].apply(
            lambda arr: next((c for c in arr if c in code_set), None)
        )

    # --------------------------------------------------------------------
    # 7) (Opcional) Columnas auxiliares para debugging
    # --------------------------------------------------------------------
    out["events_raw"] = out["codes"].apply(
        lambda arr: [c for c in arr if any(c in code_set for code_set in raw_map.values())]
    )

    out["events_from_to"] = out["codes"].apply(
        lambda arr: [c for c in arr if any(c in code_set for code_set in ft_map.values())]
    )

    logging.info(f"[expand_event_codes] timestamps únicos → {len(out)}")

    # --------------------------------------------------------------------
    # 8) Restaurar índice Timestamp
    # --------------------------------------------------------------------
    out = out.set_index(ts_col)

    return out
