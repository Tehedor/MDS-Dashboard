# utils/helpers.py
import yaml
from pathlib import Path

# -----------------------------------------------------------
# Cargar YAML
# -----------------------------------------------------------
def load_config(path: Path):
    if path is None:
        raise ValueError("El path no puede ser None")
    if isinstance(path, str):
        path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)



# -----------------------------------------------------------
# GENERAR OPCIONES DEL CHECKLIST
# cols_all = estructura JSON del get_all_columns()["all"]
# -----------------------------------------------------------
def build_checklist_options(cols_all):
    """
    Devuelve cada opción con su metadata incluida.
    Ejemplo:
    {
        "label": "Battery_Active_Power (Battery)",
        "value": "Battery::tabular::Battery_Active_Power",
        "meta": { ... item original ... }
    }
    """
    opciones = []

    for item in cols_all:
        name = item.get("name")
        tipo = item.get("type")
        comp = item.get("component")

        if not name or not tipo:
            continue

        # ----- TABULAR -----
        if tipo == "tabular":
            label = f"{name} ({comp})"
            value = f"{comp}::{tipo}::{name}"

        # ----- EVENTOS -----
        elif tipo in ("raw", "from_to"):
            label = f"{item['measurement']} [{tipo}] ({comp})"
            value = f"{comp}::{tipo}::{item['name']}"

        else:
            continue

        opciones.append({
            "label": label,
            "value": value,
            "meta": item   # 🔥 clave: guardamos metadata completa
        })

    return opciones


def get_tabular_type(item, components_meta):
    comp = item.get("component")
    meas = item.get("name")

    comp_data = components_meta.get(comp, {})
    measurement_meta = comp_data.get("measurements", {}).get(meas)

    if measurement_meta:
        return measurement_meta.get("type")  # potencia, voltaje, frecuencia, temperatura...

    return None



# -----------------------------------------------------------
# GENERAR OPCIONES DEL DROPDOWN "TIPO"
# usando components_meta
# -----------------------------------------------------------
def build_tipo_options(components_meta):
    tipos = set()

    # Extraemos los tipos reales del dataset:
    # potencia, voltaje, frecuencia, temperatura, …
    for comp_data in components_meta.values():
        for meta in comp_data.get("measurements", {}).values():
            t = meta.get("type")
            if t:
                tipos.add(t)

    # Añadir también los eventos
    tipos.update(["raw", "from_to", "tabular"])

    return [{"label": t.capitalize(), "value": t} for t in sorted(tipos)]



# -----------------------------------------------------------
# Helpers para labels
# -----------------------------------------------------------
def get_measurement_info_from_components(components_dict, value_code):
    """
    Dado el value del checklist, devuelve:
        {component, measurement, mode}
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

    else:  # tabular simple
        for comp_id, comp in components_dict.items():
            meas = comp.get("measurements", {})
            if value_code in meas or any(value_code == v.get("display_name") for v in meas.values()):
                return {"component": comp.get("name", comp_id), "measurement": value_code, "mode": None}

        return None



def format_label_with_unit(components_dict, measurement_name):
    info = get_measurement_info_from_components(components_dict, measurement_name)
    if info:
        for comp_id, comp_data in components_dict.items():
            if comp_data.get("name") == info["component"]:
                meas_meta = comp_data.get("measurements", {}).get(info["measurement"])
                if meas_meta:
                    unit = meas_meta.get("unit")
                    display = meas_meta.get("display_name", info["measurement"])
                    return f"{display} [{unit}]" if unit else display
    return measurement_name
