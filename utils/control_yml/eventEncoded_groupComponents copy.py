import re
import yaml
from collections import defaultdict
import os
import json
from typing import Union

def group_components_to_yaml_file(path_file: Union[str, dict], output_file: str = "control_groupedDictionary.yml", input_path: str = None) -> bool:
    """
    Recibe un diccionario o la ruta a un JSON con claves tipo QXX y from_QXX_to_QYY,
    genera la estructura agrupada y la guarda en un archivo YAML.

    - Si path_file es dict, lo usa directamente.
    - Si path_file es str, lo interpreta como ruta al JSON y lo carga.
    - Si se pasa input_path (o path_file es ruta) el output se colocará en el mismo directorio del input.
    Devuelve True si se genera el YAML correctamente, False en caso contrario.
    """
    try:
        # Cargar data (acepta dict o ruta)
        if isinstance(path_file, dict):
            data = path_file
            input_abs = os.path.abspath(input_path) if input_path else None
        else:
            input_abs = os.path.abspath(path_file)
            if not os.path.isfile(input_abs):
                print(f"Error: no existe el fichero de entrada: {input_abs}")
                return False
            with open(input_abs, "r", encoding="utf-8") as f:
                data = json.load(f)

        grouped = defaultdict(lambda: {"raw": {}, "from_to": {}})

        # RAW: NombreComponente_QXX  (excluye los que tienen "from")
        raw_pattern = re.compile(r"^(?!.*from)(.*)_Q(\d+)$")

        # FROM_TO: NombreComponente_from_QXX_to_QYY
        from_pattern = re.compile(r"^(.*)_from_Q(\d+)_to_Q(\d+)$")

        for key, value in data.items():
            # FROM_TO primero
            m_from = from_pattern.match(key)
            if m_from:
                component = m_from.group(1)
                q_from = f"Q{m_from.group(2)}"
                q_to = f"Q{m_from.group(3)}"
                grouped[component]["from_to"][f"{q_from}_to_{q_to}"] = value
                continue

            # RAW después
            m_raw = raw_pattern.match(key)
            if m_raw:
                component = m_raw.group(1)
                q_value = f"Q{m_raw.group(2)}"
                grouped[component]["raw"][q_value] = value
                continue

        # Convertir a dict normal
        grouped = dict(grouped)

        # Envolver todo bajo la clave 'components'
        output_dict = {"components": grouped}

        # Determinar ruta de salida: si se proporcionó input_path (o path_file era ruta), usar su directorio
        if input_abs:
            input_dir = os.path.dirname(os.path.abspath(input_abs))
            output_path = os.path.join(input_dir, output_file)
        else:
            output_path = output_file

        # Asegurar que el directorio de salida existe
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # Guardar YAML con la estructura deseada
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(output_dict, f, allow_unicode=True, sort_keys=True, default_flow_style=False)

        print(f"Archivo YAML generado correctamente: {output_path}")
        return True

    except Exception as e:
        print("Error generando YAML:", type(e).__name__, e)
        return False


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Agrupa claves Qxx de un JSON y genera YAML.")
    parser.add_argument("input", help="Ruta al JSON de entrada (p. ej. Events_Dictionary.json)")
    parser.add_argument("-o", "--output", default="control_groupedDictionary.yml", help="Nombre del archivo YAML de salida")
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)

    # Ahora la función se encarga de crear el output en el mismo directorio que el input
    group_components_to_yaml_file(input_path, output_file=args.output, input_path=input_path)

    print("Directorio actual (cwd):", os.getcwd())
    print("YAML creado en:", os.path.join(os.path.dirname(input_path), args.output))