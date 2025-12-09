# utils/dataset/loader.py
import logging
from pathlib import Path
import pandas as pd
import json
from utils.helpers import load_config
from utils.data_loader import cargar_dataset_completo
import logging
from debug.debug import save_debug_info

def load_or_build_parquet(subdataset):
    """
    subdataset: instancia de SubDataset
    """

    parquet = subdataset.parquet_file
    if parquet.exists():
        logging.info(f"📦-Parquet ya existe para SubDataset '{subdataset.name}': {parquet}")
        return

    logging.info(f"📦-Construyendo parquet para SubDataset '{subdataset.name}'")
    parquet.parent.mkdir(parents=True, exist_ok=True)

    t = subdataset.type

    if t == "tabular":
        _build_tabular(subdataset)
    elif t == "event-encoded":
        _build_event_encoded(subdataset)
    else:
        raise ValueError(f"Tipo de dataset desconocido: {t}")

# -----------------------------------------
def _build_tabular(sd):
    """
    Construye el parquet de un subdataset TABULAR aplicando toda la pipeline
    de limpieza definida en su control_dataset.yml.
    """
    # Obtener lista de CSV raw
    raw_files = list(sd.raw_dir.glob("*.csv"))
    if not raw_files:
        raise RuntimeError(f"No se encontraron CSV en {sd.raw_dir}")

    # Path completo de control_dataset.yml
    control_path = sd.control_path
    config = load_config(control_path)

    pipeline_cfg = config.get("pipelineCleanData", {})
    timestamp_col = sd.timestamp_col

    # Ejecutar la pipeline EXACTA del user
    df_clean = cargar_dataset_completo(
        pattern_csv=[str(f) for f in raw_files],
        pipelineCleanData=pipeline_cfg,
        timestamp_col=timestamp_col,
    )

    # Asegurar columna timestamp presente y tipo datetime
    if timestamp_col not in df_clean.columns:
        raise ValueError(
            f"❌ Después de la pipeline no existe la columna '{timestamp_col}' en {sd.name}"
        )
    df_clean[timestamp_col] = pd.to_datetime(df_clean[timestamp_col], errors="coerce")

    # Reset index si pipeline dejó Timestamp como índice
    if isinstance(df_clean.index, pd.DatetimeIndex):
        df_clean = df_clean.reset_index().rename(columns={"index": timestamp_col})

    # Escribir parquet final
    df_clean.to_parquet(sd.parquet_file, index=True)

    print(f"✔ Parquet generado con pipeline: {sd.parquet_file}   filas={len(df_clean)}")

def _build_event_encoded(sd):
    """
    Construye el parquet de un subdataset 'event-encoded' según el nuevo YAML agrupado.
    Resultado en sd.parquet_file con columnas:
      - Timestamp (columna)
      - events_state (list[int])
      - events_from_to (list[int])
      - <measurement>_state (int or None)   # scalar por medida
      - <measurement>_from_to (int or None) # scalar por medida
    """
    raw_files = list(sd.raw_dir.glob("*.csv"))
    if not raw_files:
        raise RuntimeError(f"No CSV en {sd.raw_dir}")

    # 1) ejecutar pipeline del subdataset como antes
    config = load_config(sd.control_file)
    pipeline_cfg = config.get("pipelineCleanData", {})
    timestamp_col = sd.timestamp_col

    df = cargar_dataset_completo(
        pattern_csv=[str(f) for f in raw_files],
        pipelineCleanData=pipeline_cfg,
        timestamp_col=timestamp_col
    )

    # 2) La pipeline debe entregar un DatetimeIndex (según diseño original)
    if not isinstance(df.index, pd.DatetimeIndex):
        raise RuntimeError(
            f"❌ Se esperaba DatetimeIndex tras la pipeline en {sd.name}, pero obtuvimos: {type(df.index)}"
        )

    # 3) Pasar índice a columna Timestamp
    df = df.reset_index().rename(columns={"index": timestamp_col})

    # 4) La pipeline debe devolver columna 'event' -> renombrar a 'event_code'
    if "event" not in df.columns:
        raise RuntimeError(
            f"❌ La pipeline no devolvió columna 'event' en {sd.name}. Columnas={list(df.columns)}"
        )
    df = df.rename(columns={"event": "event_code"})

    # 5) Mantener solo Timestamp y event_code (queremos agrupar y pivotar)
    df = df[[timestamp_col, "event_code"]]

    # 6) Cargar YAML agrupado (control_groupedDictionary.yml) para saber qué códigos pertenecen a qué medida
    #    Intentamos leerlo desde la carpeta del subdataset (sd.path) y, si no, desde root/Epoch-Dataset.
  
    grouped_cfg = sd.componentes
    # with open(grouped_path, "r", encoding="utf-8") as f:
    #     grouped_cfg = yaml.safe_load(f)

    # 7) Normalizar estructura del YAML y construir:
    #    components_map = {
    #       "<measurement>": {"raw": set(...), "from_to": set(...)},
    #       ...
    #    }
    components_map = {}

    comps_node = grouped_cfg.get("components", {})
    # el YAML puede tener dos estilos: (a) comp->measurements-><measure_name>->measurements-><...>
    # o (b) comp-><measure_name>->measurements-><...>
    for comp_key, comp_val in comps_node.items():
        # localizar bloque 'measurements' que contenga las mediciones reales
        meas_block = comp_val.get("measurements") if isinstance(comp_val, dict) else None

        # si no hay 'measurements' al nivel del componente, es posible que las mediciones estén directamente
        # bajo comp_val (en algunas variantes de tu YAML).
        if not meas_block:
            # si comp_val itself is a mapping of measurements, use it
            if isinstance(comp_val, dict):
                # skip 'name' if present
                possible = {k: v for k, v in comp_val.items() if k != "name"}
                # if possible has a 'measurements' key inside each entry, normalize:
                if "measurements" in possible:
                    meas_block = possible["measurements"]
                else:
                    # assume that possible keys are measurement names
                    meas_block = possible

        if not meas_block:
            continue

        for measure_name, measure_entry in meas_block.items():
            # measure_entry may either have 'measurements' inside (your modified format)
            inner = measure_entry.get("measurements") if isinstance(measure_entry, dict) else None
            if inner:
                # inner contains keys like "<measurement>-raw" and "<measurement>-from_to"
                raw_codes = set()
                from_to_codes = set()
                for k, v in inner.items():
                    # v expected to contain 'columns_encoded'
                    encoded = v.get("columns_encoded") if isinstance(v, dict) else None
                    if not encoded:
                        continue
                    if k.endswith("-raw"):
                        raw_codes.update(encoded)
                    elif k.endswith("-from_to") or k.endswith("from_to"):
                        from_to_codes.update(encoded)
                # use canonical measurement base name (strip suffixes)
                base_measure = measure_entry.get("name", measure_name)
                components_map[base_measure] = {
                    "raw": raw_codes,
                    "from_to": from_to_codes
                }
            else:
                # fallback: measure_entry might directly contain raw/from_to keys (older format)
                try:
                    raw_codes = set(measure_entry["raw"]["columns_encoded"])
                except Exception:
                    raw_codes = set()
                try:
                    from_to_codes = set(measure_entry["from_to"]["columns_encoded"])
                except Exception:
                    from_to_codes = set()

                base_measure = measure_entry.get("name", measure_name) if isinstance(measure_entry, dict) else measure_name
                components_map[base_measure] = {
                    "raw": raw_codes,
                    "from_to": from_to_codes
                }

    # 8) Preparar sets globales
    all_raw_codes = set()
    all_from_to_codes = set()
    for m, groups in components_map.items():
        all_raw_codes.update(groups["raw"])
        all_from_to_codes.update(groups["from_to"])

    # 9) Agrupar eventos por timestamp -> lista de event_code
    grouped = (
        df.groupby(timestamp_col)["event_code"]
          .apply(list)
          .rename("events")
          .reset_index()
    )

    # 10) Vamos a construir el DataFrame final: tomamos todos los timestamps
    #     Si quieres mantener ALL timestamps incluso sin eventos, deberías partir de una tabla base.
    #     Aquí partimos de 'grouped' (sólo timestamps con eventos) y luego nos aseguramos de mantener el
    #     resto en el pipeline (si tu main timestamps vienen de otro sitio, el composite se encargará).
    out = grouped.copy()

    # 11) Añadir columnas globales (arrays) filtradas
    out["events_state"] = out["events"].apply(lambda lst: sorted([int(e) for e in lst if int(e) in all_raw_codes]))
    out["events_from_to"] = out["events"].apply(lambda lst: sorted([int(e) for e in lst if int(e) in all_from_to_codes]))

    # 12) Añadir columnas por cada medida (scalar: min or None). Nombre: <measurement>_state and <measurement>_from_to
    def scalar_from_list(lst):
        """Si la lista está vacía -> None; si hay varios -> elegir el menor (determinista)."""
        if not lst:
            return None
        return int(min(lst))

    for measure, groups in components_map.items():
        raw_set = groups["raw"]
        ft_set = groups["from_to"]

        col_state = f"{measure}_state"
        col_ft = f"{measure}_from_to"

        out[col_state] = out["events"].apply(lambda lst, s=raw_set: scalar_from_list([int(e) for e in lst if int(e) in s]))
        out[col_ft] = out["events"].apply(lambda lst, s=ft_set: scalar_from_list([int(e) for e in lst if int(e) in s]))

    # 13) Selección final de columnas
    out = out.drop(columns=["events"])

    final_cols = (
        [timestamp_col, "events_state", "events_from_to"] +
        [
            c for c in out.columns
            if (c.endswith("_state") or c.endswith("_from_to"))
            and c not in ("events_state", "events_from_to")
        ]
    )

    out = out[final_cols]

    # 14) Guardar parquet
    out.to_parquet(sd.parquet_file, index=False)
    print(f"✔ Parquet de eventos generado: {sd.parquet_file} | filas={len(out)}")

    save_debug_info(
        content_source=out.head(20),
        filename=f"debug_{sd.name}_event_encoded_head.txt",
        head=f"# head of event-encoded parquet for {sd.name}"
    )

    return
