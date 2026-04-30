#!/usr/bin/env python3
import yaml
import json  # Import necesario para leer metadata
from pathlib import Path
from config_env import settings_env 

# ============================================================
# 🌍 ENVIRONMENT VARIABLES (with defaults)
# ============================================================
EXECUTIONS_ROOT = Path(settings_env.EXECUTIONS_ROOT)
EXPLORE_STAGE = settings_env.EXPLORE_STAGE
EVENTS_STAGE = settings_env.EVENTS_STAGE
DEFAULT_DATASET = settings_env.DEFAULT_DATASET

TIMESTAMP_COL = settings_env.TIMESTAMP_COL
OUTPUT_CONTROL = Path(settings_env.OUTPUT_CONTROL)
CONTROL_DATASET_FILE = settings_env.CONTROL_DATASET_FILE
EPOCH_MODE = settings_env.EPOCH_MODE

# ============================================================
# 🧾 YAML OUTPUT FORMATTER
# ============================================================

def format_control_yaml(yaml_text: str) -> str:
    lines = yaml_text.splitlines()
    out: list[str] = []

    in_section = None
    section_indent = None
    seen_first_child = False

    for line in lines:
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)

        is_top_level_key = indent == 0 and ":" in stripped

        if is_top_level_key:
            key = stripped.split(":", 1)[0]

            if key in {"subdatasets", "Datasets", "default_dataset"} and out and out[-1] != "":
                out.append("")

            if stripped.endswith(":"):
                in_section = key
                section_indent = None
                seen_first_child = False
            else:
                in_section = None
                section_indent = None
                seen_first_child = False

            out.append(line)
            continue

        if in_section is not None:
            if section_indent is None and stripped and indent > 0:
                section_indent = indent

            if (
                in_section in {"subdatasets", "Datasets"}
                and section_indent is not None
                and indent == section_indent
                and stripped.endswith(":")
            ):
                if seen_first_child and out and out[-1] != "":
                    out.append("")
                seen_first_child = True
                out.append(line)
                continue

        out.append(line)

    return "\n".join(out) + "\n"

# ============================================================
# 🛠️ HELPERS
# ============================================================

def discover_variants(stage_path: Path) -> dict:
    """
    Descubre variantes desde directorios hijos tipo v1_0001.

    Mantiene compatibilidad con el esquema antiguo basado en variants.yaml,
    pero prioriza el layout nuevo donde cada variante vive en su propia carpeta.
    """
    variants_file = stage_path / "variants.yaml"
    if variants_file.exists():
        with open(variants_file, "r", encoding="utf-8") as f:
            legacy_variants = yaml.safe_load(f) or {}
        variants = legacy_variants.get("variants", {})
        if variants:
            return variants

    if not stage_path.exists():
        return {}

    discovered = {}
    for variant_dir in sorted(
        path for path in stage_path.iterdir() if path.is_dir() and path.name.startswith("v")
    ):
        parquet = find_parquet_from_params(variant_dir)
        if parquet is None:
            continue

        discovered[variant_dir.name] = {
            "path": variant_dir,
            "parquet_path": parquet,
        }

    return discovered

def find_parquet_from_params(
    version_dir: Path,
) -> Path | None:
    if not version_dir.exists():
        return None

    preferred = sorted(version_dir.rglob("*_dataset.parquet"))
    if preferred:
        return preferred[0]

    parquets = sorted(version_dir.rglob("*.parquet"))
    if parquets:
        return parquets[0]

    return None

def version_key(version: str) -> str:
    return version.replace("v", "")

def get_epoch_parent_variant(parquet_path: Path) -> str | None:
    """
    Lee el archivo 02_prepareeventsds_metadata.json situado junto al parquet
    para averiguar de qué dataset temporal depende (parent_variant).
    """
    # Asumimos que el metadata json está en el mismo directorio que el parquet
    # o en el directorio de la versión. Buscamos en el directorio del parquet.
    parent_dir = parquet_path.parent

    metadata_candidates = [parent_dir / candidate for candidate in settings_env.CTRL_COMPONENTS_EPOCH_METADATA_CANDIDATES]
    preferred_metadata = parent_dir / settings_env.CTRL_COMPONENTS_EPOCH_METADATA
    if preferred_metadata not in metadata_candidates:
        metadata_candidates.insert(0, preferred_metadata)

    seen_files = set()

    for metadata_file in metadata_candidates:
        if metadata_file in seen_files or not metadata_file.exists():
            continue
        seen_files.add(metadata_file)

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                if metadata_file.suffix.lower() == ".json":
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)

            parent_variant = _find_nested_value(data, ("parent_variant", "parent"))
            if parent_variant:
                return str(parent_variant)
        except Exception as e:
            print(f"⚠️ Error leyendo metadata en {metadata_file}: {e}")

    return None


def _find_nested_value(data, keys: tuple[str, ...]):
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if value:
                return value

        for value in data.values():
            nested = _find_nested_value(value, keys)
            if nested is not None:
                return nested

    if isinstance(data, list):
        for item in data:
            nested = _find_nested_value(item, keys)
            if nested is not None:
                return nested

    return None

def generate_control_yml() -> Path:
    # ============================================================
    # 🔍 DISCOVER DATASETS
    # ============================================================

    subdatasets = {}
    tabular_versions = {} # map: version_key -> subdataset_name
    epoch_versions = {}   # map: version_key -> dict {name: subdataset_name, path: Path}

    # ---------- TABULAR ----------
    explore_stage_root = EXECUTIONS_ROOT / EXPLORE_STAGE
    explore_variants = discover_variants(explore_stage_root)

    for v, meta in explore_variants.items():
        parquet = find_parquet_from_params(
            Path(meta.get("path", explore_stage_root / v)),
        )
        if parquet is None:
            continue
        name = f"MDS-Dataset-{v}"
        subdatasets[name] = {
            "type": "tabular",
            "path": str(parquet),
            "control_file": CONTROL_DATASET_FILE,
            "timestamp_col": TIMESTAMP_COL,
        }
        tabular_versions[version_key(v)] = name

    # ---------- EPOCH ----------
    events_stage_root = EXECUTIONS_ROOT / EVENTS_STAGE
    events_variants = discover_variants(events_stage_root)

    for v, meta in events_variants.items():
        parquet = find_parquet_from_params(
            Path(meta.get("path", events_stage_root / v)),
        )
        if parquet is None:
            continue
        name = f"Epoch-Dataset-{v}"
        subdatasets[name] = {
            "type": "event-encoded",
            "path": str(parquet),
            "control_file": CONTROL_DATASET_FILE,
            "timestamp_col": TIMESTAMP_COL,
            "merge_on": TIMESTAMP_COL,
            "strategy": "sparse-columns",
        }
        # Guardamos el path también para buscar el metadata después
        epoch_versions[version_key(v)] = {
            "name": name, 
            "path": parquet
        }

    # ============================================================
    # 🔗 BUILD FINAL DATASETS
    # ============================================================

    datasets = {}

    # 1. Datasets Tabulares Puros (Base)
    for tab_v, tab_name in tabular_versions.items():
        datasets[f"MDS-Complete-v{tab_v}"] = {
            "subdatasets": {
                "main": tab_name,
                "epoch": None,
            }
        }

    # 2. Datasets Combinados (Eventos ligados a su Padre)
    if EPOCH_MODE:
        for epoch_v, epoch_info in epoch_versions.items():
            epoch_name = epoch_info["name"]
            epoch_path = epoch_info["path"]
            
            # Buscamos dependencia explícita en metadata
            parent_variant_full = get_epoch_parent_variant(epoch_path) # Ej: "v003"
            
            if parent_variant_full:
                parent_key = version_key(parent_variant_full) # "003"
                
                # Verificamos si tenemos cargado ese dataset temporal
                if parent_key in tabular_versions:
                    tab_name = tabular_versions[parent_key]
                    
                    # Nuevo Naming Convention: ...-Tv{Temporal}_Ev{Events}
                    combined_name = f"MDS-Complete-Tv{parent_key}_Ev{epoch_v}"
                    
                    datasets[combined_name] = {
                        "subdatasets": {
                            "main": tab_name,
                            "epoch": epoch_name,
                        }
                    }
                else:
                    print(f"⚠️ El dataset de eventos {epoch_name} requiere temporal {parent_variant_full}, pero no se encontró.")

    if not subdatasets:
        print(
            "⚠️ No se encontraron parquets para construir control.yml. "
            "Se generará un archivo vacío y se omitirán los datasets ausentes."
        )

    # ============================================================
    # 🎯 VALIDATE DEFAULT DATASET
    # ============================================================
    
    final_default_dataset = DEFAULT_DATASET
    
    # Comprobamos si el default existe en la lista de compuestos.
    if final_default_dataset not in datasets:
        if datasets:
            # Cogemos el primero de la lista (normalmente será el temporal v100 si es el primero cargado)
            final_default_dataset = list(datasets.keys())[0]
            print(f"[*] DEFAULT_DATASET '{DEFAULT_DATASET}' no está en la lista de conjuntos compuestos. Usando fallback: '{final_default_dataset}'")
        else:
            final_default_dataset = None

    # ============================================================
    # 📝 WRITE control.yml
    # ============================================================

    control = {
        "version": "1.0",
        "description": "Control maestro de los datasets del sistema",
        "subdatasets": subdatasets,
        "Datasets": datasets,
        "default_dataset": final_default_dataset,
    }

    OUTPUT_CONTROL.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_CONTROL, "w") as f:
        yaml_text = yaml.safe_dump(control, sort_keys=False, default_flow_style=False)
        f.write(format_control_yaml(yaml_text))

    print(f"✅ control.yml generado correctamente en: {OUTPUT_CONTROL}")
    return OUTPUT_CONTROL


if __name__ == "__main__":
    generate_control_yml()