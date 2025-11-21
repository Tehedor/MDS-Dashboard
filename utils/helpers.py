# utils/helpers.py
import yaml
from pathlib import Path

def load_config(path: Path):
    """Carga un YAML desde path (Path o str)."""
    if isinstance(path, (str,)):
        path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def build_checklist_options_from_components(components_dict, dataset_type, duckdb_columns):
    """
    Devuelve una lista de opciones para dcc.Checklist basadas en:
      - components_dict: dict con estructura 'components' (como en tus YAMLs)
      - dataset_type: 'TabularDataSet' o 'EventEncodedDataSet'
      - duckdb_columns: lista de columnas reales (para evitar mostrar cols inexistentes)
    """
    options = []

    if not components_dict:
        # fallback: todas las columnas excepto Timestamp
        for c in duckdb_columns:
            if c.lower() != "timestamp":
                options.append({"label": c, "value": c})
        return options

    for comp_id, comp in components_dict.items():
        measurements = comp.get("measurements", {})

        # EventEncoded: measurements contains groups raw/from_to with columns lists (names)
        if dataset_type == "EventEncodedDataSet":
            for meas_id, meas_info in measurements.items():
                if "raw" in meas_info:
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
    if not components_dict:
        return None

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

def format_label_with_unit(components_dict, measurement_name):
    """
    Devuelve la etiqueta formateada con unidad si existe en components_dict.
    """
    info = get_measurement_info_from_components(components_dict, measurement_name)
    if info:
        comp = components_dict.get(info["component"], {})
        # buscar unidad si existe
        comp_entry = None
        # components_dict keys are comp_id; info['component'] contains display name; we attempt matching
        for comp_id, comp_data in components_dict.items():
            if comp_data.get("name") == info["component"] or comp_id == info.get("component"):
                comp_entry = comp_data
                break
        if comp_entry:
            meas_meta = comp_entry.get("measurements", {}).get(info["measurement"])
            if meas_meta:
                unit = meas_meta.get("unit")
                display = meas_meta.get("display_name", info["measurement"])
                if unit:
                    return f"{display} [{unit}]"
                return display
    # fallback
    return measurement_name
