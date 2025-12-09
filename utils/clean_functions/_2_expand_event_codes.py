import logging
import pandas as pd
# ...existing code...
def expand_event_codes(subdataset):
    """
    Convierte un dataset epoch (Timestamp, event) en columnas por medida.
    Usa:
       - subdataset.df              → dataframe con 'event' o 'event_id'
       - subdataset.componentes     → ctl_components.yml generado
    """

    df = subdataset.df
    ctl = subdataset.componentes   # YA lo tienes en memoria

    # aceptar 'event' o 'event_id'
    if "event" in df.columns:
        event_col = "event"
    elif "event_id" in df.columns:
        event_col = "event_id"
    else:
        raise RuntimeError("expand_event_codes() → falta columna 'event' o 'event_id'")

    # ------------------------------------------------------------
    # Recolectamos mapas raw y from_to desde ctl_components.yml
    # ------------------------------------------------------------
    raw_map = {}
    ft_map = {}

    for comp, compdata in ctl["components"].items():
        meas = compdata["measurements"]

        for mname, mdata in meas.items():
            codes = set(mdata["encodes"])
            if mdata["type"] == "event":
                raw_map[mname] = codes
            elif mdata["type"] == "from_to":
                ft_map[mname] = codes

    # ------------------------------------------------------------
    # Agrupar múltiples filas por timestamp: df.index → lista de códigos
    # ------------------------------------------------------------
    grouped = df.groupby(df.index)[event_col].apply(list).reset_index()
    grouped = grouped.rename(columns={event_col: "codes"})

    out = grouped.copy()

    # ------------------------------------------------------------
    # Crear columnas raw
    # ------------------------------------------------------------
    for name, code_set in raw_map.items():
        out[name] = out["codes"].apply(
            lambda arr: next((c for c in arr if c in code_set), None)
        )

    # ------------------------------------------------------------
    # Crear columnas from_to
    # ------------------------------------------------------------
    for name, code_set in ft_map.items():
        out[name] = out["codes"].apply(
            lambda arr: next((c for c in arr if c in code_set), None)
        )

    # ------------------------------------------------------------
    # Columnas agregadas
    # ------------------------------------------------------------
    out["events_raw"] = out["codes"].apply(
        lambda arr: [c for c in arr if any(c in s for s in raw_map.values())]
    )

    out["events_from_to"] = out["codes"].apply(
        lambda arr: [c for c in arr if any(c in s for s in ft_map.values())]
    )

    logging.info(f"[expand_event_codes] timestamps únicos → {len(out)}")

    # El pipeline espera un DF con índice timestamp
    idx_col = df.index.name if df.index.name else "index"
    out = out.set_index(idx_col)

    return out