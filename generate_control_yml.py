#!/usr/bin/env python3
import os
import yaml
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

def load_variants(stage_path: Path) -> dict:
    variants_file = stage_path / "variants.yaml"
    if not variants_file.exists():
        return {}
    with open(variants_file, "r") as f:
        return yaml.safe_load(f).get("variants", {})

def find_parquet_from_params(
    version: str,
    params_path: Path,
    stage_root: Path,
) -> Path | None:
    """
    Resuelve el directorio de versión de forma portable:
    - Ignora rutas absolutas del host
    - Usa SIEMPRE el stage_root montado en el contenedor
    """

    # Siempre confiar en el layout del stage_root
    version_dir = stage_root / version

    if not version_dir.exists():
        return None

    for parquet in version_dir.rglob("*.parquet"):
        return parquet

    return None



def version_key(version: str) -> str:
    return version.replace("v", "")


def dependency_key(version: str) -> str:
    return f"{int(version_key(version)) % 10:03d}"

def generate_control_yml() -> Path:
    # ============================================================
    # 🔍 DISCOVER DATASETS
    # ============================================================

    subdatasets = {}
    tabular_versions = {}
    epoch_versions = {}

    # ---------- TABULAR ----------
    explore_stage_root = EXECUTIONS_ROOT / EXPLORE_STAGE
    explore_variants = load_variants(explore_stage_root)

    for v, meta in explore_variants.items():
        parquet = find_parquet_from_params(
            version=v,
            params_path=Path(meta["params_path"]),
            stage_root=explore_stage_root,
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
    events_variants = load_variants(events_stage_root)

    for v, meta in events_variants.items():
        parquet = find_parquet_from_params(
            version=v,
            params_path=Path(meta["params_path"]),
            stage_root=events_stage_root,
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
        epoch_versions[version_key(v)] = name

    # ============================================================
    # 🔗 BUILD FINAL DATASETS (CORRECTO)
    # ============================================================

    datasets = {}

    for tab_v, tab_name in tabular_versions.items():
        # Base dataset (no epoch)
        datasets[f"MDS-Complete-v{tab_v}"] = {
            "subdatasets": {
                "main": tab_name,
                "epoch": None,
            }
        }

        # All epochs that depend on this tabular
        if EPOCH_MODE:
            for epoch_v, epoch_name in epoch_versions.items():
                # Convertimos ambos a int para que la comparación sea numérica y no de texto
                try:
                    dep_id = int(version_key(f"v{epoch_v}")) % 10
                    tab_id = int(tab_v)
                    
                    if dep_id == tab_id:
                        datasets[f"MDS-Complete-v{epoch_v}"] = {
                            "subdatasets": {
                                "main": tab_name,
                                "epoch": epoch_name,
                            }
                        }
                except ValueError:
                    continue # Salta si la versión no es numérica

    if not subdatasets:
        raise RuntimeError(
            "No se encontraron parquets para construir control.yml. "
            "Revisa EXECUTIONS_ROOT/variants.yaml y los volúmenes montados."
        )

    # ============================================================
    # 📝 WRITE control.yml
    # ============================================================

    control = {
        "version": "1.0",
        "description": "Control maestro de los datasets del sistema",
        "subdatasets": subdatasets,
        "Datasets": datasets,
        "default_dataset": DEFAULT_DATASET,
    }

    OUTPUT_CONTROL.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_CONTROL, "w") as f:
        yaml_text = yaml.safe_dump(control, sort_keys=False, default_flow_style=False)
        f.write(format_control_yaml(yaml_text))

    print(f"✅ control.yml generado correctamente en: {OUTPUT_CONTROL}")
    return OUTPUT_CONTROL


if __name__ == "__main__":
    generate_control_yml()
