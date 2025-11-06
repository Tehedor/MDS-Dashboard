# utils/helpers.py
import yaml

def load_config(config_path="./components.yml"):
    """Carga la configuración YAML de los componentes."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_measurement_info(config, measurement_name):
    """Obtiene la información de un measurement (nombre y unidad)."""
    for comp_id, comp_data in config['components'].items():
        if measurement_name in comp_data['measurements']:
            return {
                'component': comp_data['name'],
                'info': comp_data['measurements'][measurement_name]
            }
    return None

def format_label_with_unit(config, measurement_name):
    """Devuelve la etiqueta con unidad formateada."""
    info = get_measurement_info(config, measurement_name)
    if info:
        return f"{info['info']['display_name']} [{info['info']['unit']}]"
    return measurement_name
