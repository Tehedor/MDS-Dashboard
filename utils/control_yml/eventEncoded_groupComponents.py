import re
import yaml
from collections import defaultdict
import os
import json
from typing import Union

# ---------- Representer para LISTAS EN INLINE ----------
class InlineList(list):
    pass

def inline_list_representer(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)

yaml.add_representer(InlineList, inline_list_representer)
# --------------------------------------------------------


def group_components_to_yaml_file(
    path_file: Union[str, dict],
    output_file: str = "control_groupedDictionary.yml",
    mode: str = "compact",        # "old" / "compact" / "long"
    input_path: str = None
) -> bool:

    try:
        # ----------- Cargar data ----------------
        if isinstance(path_file, dict):
            data = path_file
            input_abs = os.path.abspath(input_path) if input_path else None
        else:
            input_abs = os.path.abspath(path_file)
            if not os.path.isfile(input_abs):
                print(f"❌ Error: no existe el fichero de entrada: {input_abs}")
                return False
            with open(input_abs, "r", encoding="utf-8") as f:
                data = json.load(f)

        grouped_raw = defaultdict(dict)
        grouped_ft = defaultdict(dict)

        raw_pattern = re.compile(r"^(?!.*from)(.*)_Q(\d+)$")
        ft_pattern  = re.compile(r"^(.*)_from_Q(\d+)_to_Q(\d+)$")

        # Clasificación
        for key, value in data.items():

            m_raw = raw_pattern.match(key)
            if m_raw:
                comp = m_raw.group(1)
                q = f"Q{m_raw.group(2)}"
                grouped_raw[comp][q] = value
                continue

            m_ft = ft_pattern.match(key)
            if m_ft:
                comp = m_ft.group(1)
                qf = f"Q{m_ft.group(2)}"
                qt = f"Q{m_ft.group(3)}"
                grouped_ft[comp][f"{qf}_to_{qt}"] = value
                continue

        output = {"components": {}}

        # ---------------------- MODO OLD ----------------------
        if mode == "old":
            for comp in sorted(grouped_raw.keys() | grouped_ft.keys()):
                output["components"][comp] = {
                    "raw": grouped_raw.get(comp, {}),
                    "from_to": grouped_ft.get(comp, {})
                }

        # ---------------------- MODO COMPACT ----------------------
        elif mode == "compact":
            for comp in sorted(grouped_raw.keys() | grouped_ft.keys()):
                raw_dict = grouped_raw.get(comp, {})
                ft_dict  = grouped_ft.get(comp, {})

                output["components"][comp] = {
                    "name": comp,
                    "measurements": {
                        "raw": {
                            "columns": InlineList(list(raw_dict.keys())),
                            "columns_encoded": InlineList(list(raw_dict.values()))
                        },
                        "from_to": {
                            "columns": InlineList(list(ft_dict.keys())),
                            "columns_encoded": InlineList(list(ft_dict.values()))
                        }
                    }
                }

        # ---------------------- MODO LONG ----------------------
        elif mode == "long":
            for comp in sorted(grouped_raw.keys() | grouped_ft.keys()):
                raw_dict = grouped_raw.get(comp, {})
                ft_dict  = grouped_ft.get(comp, {})

                output["components"][comp] = {
                    "name": comp,
                    "measurements": {
                        "raw": [{"name": k, "encoded": v} for k, v in raw_dict.items()],
                        "from_to": [{"name": k, "encoded": v} for k, v in ft_dict.items()]
                    }
                }

        else:
            print("❌ Modo inválido: usa 'old', 'compact' o 'long'")
            return False

        # Ruta salida
        out_path = (
            os.path.join(os.path.dirname(input_abs), output_file)
            if input_abs else output_file
        )

        # Guardar YAML
        with open(out_path, "w", encoding="utf-8") as f:
            yaml.dump(output, f, sort_keys=False, allow_unicode=True)

        print(f"✅ YAML generado correctamente: {out_path}")
        return True

    except Exception as e:
        print(f"❌ Error procesando archivo: {e}")
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