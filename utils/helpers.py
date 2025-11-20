# utils/helpers.py
# utils/helpers.py
import yaml
from pathlib import Path

def load_config(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def build_checklist_options_from_components(components_dict, dataset_type, duckdb_columns):
    """
    Devuelve una lista de opciones para dcc.Checklist basadas en:
      - components_dict: dict con estructura 'components' (como en tus YAMLs)
      - dataset_type: 'TabularDataSet' o 'EventEncodedDataSet'
      - duckdb_columns: lista de columnas reales (para evitar mostrar cols inexistentes)
    Para EventEncodedDataSet ofrecemos opciones compuestas:
      - nombre_medida (raw)  -> label "Measurement (component) [raw]"
      - nombre_medida (from_to) -> label "Measurement (component) [from_to]"
    Para TabularDataSet se ofrecen las mediciones tal cual (si están en duckdb_columns)
    """

    options = []

    for comp_id, comp in components_dict.items():
        measurements = comp.get("measurements", {})

        # EventEncoded: measurements contains groups raw/from_to with columns lists (names)
        if dataset_type == "EventEncodedDataSet":
            # Para cada medición (ej: Battery_Active_Power) puede haber 'raw' y 'from_to'
            for meas_id, meas_info in measurements.items():
                # meas_info has raw/from_to subkeys
                if "raw" in meas_info:
                    # raw -> columnas list (strings) o encoded indices
                    cols = meas_info["raw"].get("columns", [])
                    for c in cols:
                        if c in duckdb_columns:
                            options.append({
                                "label": f"{c} ({comp.get('name', comp_id)} · raw)",
                                "value": f"{comp_id}::raw::{c}"
                            })
                if "from_to" in meas_info:
                    cols = meas_info["from_to"].get("columns", [])
                    for c in cols:
                        if c in duckdb_columns:
                            options.append({
                                "label": f"{c} ({comp.get('name', comp_id)} · from_to)",
                                "value": f"{comp_id}::from_to::{c}"
                            })
        else:
            # Tabular: measurements map names to meta; we show the measurement keys if exist in DB
            for meas_key, meas_meta in measurements.items():
                # medición puede mapear a una columna con mismo nombre (display_name) o la key
                col_candidates = [meas_meta.get("display_name"), meas_key]
                for cand in col_candidates:
                    if cand and cand in duckdb_columns:
                        options.append({
                            "label": f"{meas_meta.get('display_name', meas_key)} ({comp.get('name', comp_id)})",
                            "value": cand
                        })
                        break

    # Fallback: si options queda vacío, generar options con todas las columnas reales (except Timestamp)
    if not options:
        for c in duckdb_columns:
            if c.lower() != "timestamp":
                options.append({"label": c, "value": c})

    return options


def get_measurement_info_from_components(components_dict, value_code):
    """
    Dado un value del checklist (por ejemplo 'Battery::raw::Q05' o 'MG-LV-MSB_AC_Voltage'),
    devuelve info: {'component': ..., 'measurement': ..., 'mode': 'raw'|'from_to'|None}
    """
    if "::" in value_code:
        comp_id, mode, col = value_code.split("::", 2)
        comp = components_dict.get(comp_id, {})
        return {
            "component": comp.get("name", comp_id),
            "measurement": col,
            "mode": mode
        }
    else:
        # tabular simple: buscar en components
        for comp_id, comp in components_dict.items():
            meas = comp.get("measurements", {})
            if value_code in meas or any(value_code == v.get("display_name") for v in meas.values()):
                return {"component": comp.get("name", comp_id), "measurement": value_code, "mode": None}
        return None
