# utils/control_yml/validate_config.py
import yaml
from pykwalify.core import Core

def validate_yaml(file_path: str, schema_path: str = "schema_control.yml") -> None:
    # Cargar YAML
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Validación general con PyKwalify
    core = Core(source_data=data, schema_files=[schema_path])
    core.validate(raise_exception=True)

    # Validación condicional: EventEncodedDataSet requiere Dictionary
    # Validación condicional: EventEncodedDataSet requiere 'dictionary' en metadata
    metadata = data.get("metadata", {})
    if metadata.get("type") == "EventEncodedDataSet":
        if not metadata.get("dictionary"):
            raise ValueError(
                "metadata.dictionary es obligatorio para EventEncodedDataSet"
            )

    print("Validación correcta ✅")

if __name__ == "__main__":
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(description="Validar archivo YAML contra schema")
    parser.add_argument("yaml_file", help="Archivo YAML a validar")
    # schema_file es opcional; si no se pasa se usa 'schema_control.yml'
    parser.add_argument("schema_file", nargs="?", help="Archivo de schema PyKwalify (opcional)")
    parser.add_argument("-s", "--schema", help="Ruta alternativa al schema (anula el posicional)")
    args = parser.parse_args()

    yaml_path = args.yaml_file
    # prioridad: flag -s/--schema > posicional > valor por defecto
    if args.schema:
        schema_path = args.schema
    elif args.schema_file:
        schema_path = args.schema_file
    else:
        # Si no se indica schema, buscar 'schema_control.yml' en el mismo
        # directorio donde se encuentra este script (no en el cwd desde donde se ejecute).
        script_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(script_dir, "schema_control.yml")

    yaml_path = os.path.abspath(yaml_path)
    schema_path = os.path.abspath(schema_path)

    print("Usando YAML:", yaml_path)
    print("Usando schema:", schema_path)

    if not os.path.isfile(yaml_path):
        print("Error: no existe el YAML:", yaml_path)
        sys.exit(1)
    if not os.path.isfile(schema_path):
        print("Error: no existe el schema:", schema_path)
        sys.exit(1)

    try:
        validate_yaml(yaml_path, schema_path)
    except Exception as e:
        print("Error de validación ❌:", e)
        sys.exit(1)
