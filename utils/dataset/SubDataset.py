# utils/dataset/SubDataset.py
import logging
from pathlib import Path
import pandas as pd
import yaml
import importlib
import glob
import re

from utils.helpers import load_config
from debug.debug import save_debug_info


class SubDataset:
    """
    SubDataset:
      - TabularDataSet
      - EventEncodedDataSet

    Funcionalidades:
      ✓ Limpia dataset y genera parquet al inicio
      ✗ NO mantiene df en memoria (lazy-loading real)
    """

    # ------------------------------------------------------------------
    # Regex / Parser universal para eventos (V1/V2)
    # ------------------------------------------------------------------
    EVENT_REGEX = re.compile(
        r'^(?P<component>.+?)_'
        r'(?P<q_from>Q[0-9]+)'
        r'(?:_to_(?P<q_to>Q[0-9]+))?$'
    )

    @staticmethod
    def parse_event_name(event_name: str):
        """
        Devuelve un dict estandarizado:
            {
                "component": str | None,
                "q_from": str | None,
                "q_to": str | None,
                "raw_name": str
            }
        Funciona con V1 y V2.
        """
        if not isinstance(event_name, str):
            return {"component": None, "q_from": None, "q_to": None, "raw_name": event_name}

        match = SubDataset.EVENT_REGEX.match(event_name)
        if not match:
            return {"component": None, "q_from": None, "q_to": None, "raw_name": event_name}

        gd = match.groupdict()
        return {
            "component": gd["component"],
            "q_from": gd["q_from"],
            "q_to": gd["q_to"],
            "raw_name": event_name,
        }

    # ======================================================================
    def __init__(self, name: str, root: Path, cfg: dict):
        self.name = name
        self.root = root
        self.cfg = cfg

        # ---------------------------------------------------------
        # Localización base
        # ---------------------------------------------------------
        self.path = root / cfg.get("path")
        self.control_file = self.path / cfg.get("control_file")

        # Carga del control_dataset.yml
        self.config = load_config(self.control_file)
        self.metadata = self.config.get("metadata", {})
        self.type = self.metadata.get("type", "TabularDataSet")

        # ---------------------------------------------------------
        # Crear carpeta processed y parquet final
        # ---------------------------------------------------------
        self.processed_dir = self.path / "processed"
        self.processed_dir.mkdir(exist_ok=True, parents=True)
        self.parquet_file = self.processed_dir / f"{self.name}.parquet"

        # ---------------------------------------------------------
        # Cargar componentes globales y locales
        # ---------------------------------------------------------
        self._load_components()
        self._validate_components()

        # ---------------------------------------------------------
        # EventEncoded: cargar diccionario
        # ---------------------------------------------------------
        self._load_dictionary()

        # ---------------------------------------------------------
        # Validación pipeline
        # ---------------------------------------------------------
        self._validate_clean_pipeline()

        # ---------------------------------------------------------
        # Generar archivo ctl_components.yml
        # ---------------------------------------------------------
        self._generate_ctl_components()

        # ---------------------------------------------------------
        # Ejecutar pipeline → generar parquet si no existe
        # ---------------------------------------------------------
        if not self.parquet_file.exists():
            self._load_raw_csv()
            self._run_clean_pipeline()

        if hasattr(self, "df"):
            del self.df

    # ======================================================================
    # COMPONENTES
    # ======================================================================
    def _load_components(self):
        global_components = load_config(self.root / "components.yml")
        if global_components is None:
            raise RuntimeError("No se pudo cargar components.yml global")

        self.components_global = global_components.get("components", {})
        self.timestamps_global = global_components.get("timestamps", {})

        if self.type == "TabularDataSet":
            self.components_local = self.config.get("components")
            if self.components_local is None:
                raise RuntimeError(
                    f"El subdataset '{self.name}' es Tabular pero no define 'components:'"
                )
        else:
            self.components_local = None

    def _validate_components(self):
        if self.type != "TabularDataSet":
            return True

        for comp_name in self.components_local.keys():
            if comp_name not in self.components_global:
                raise RuntimeError(
                    f"El subdataset '{self.name}' declara '{comp_name}' pero no existe en components.yml global"
                )

    # ======================================================================
    # DICTIONARY EVENTOS
    # ======================================================================
    def _load_dictionary(self):
        self.timestamp_col = self.cfg.get("timestamp_col", "Timestamp")
        self.dict_events = None

        if self.type == "EventEncodedDataSet":
            dict_path = self.metadata.get("dictionary")
            if not dict_path:
                raise RuntimeError(
                    f"El subdataset '{self.name}' es EventEncodedDataSet pero no define metadata/dictionary"
                )
            self.dict_events = load_config(self.path / dict_path)
            self.build_event_dictionary()

    # Normalizador universal Qxx / Qxx_to_Qyy
    def normalize_label(self, raw: str) -> str:
        info = self.parse_event_name(raw)

        q_from = info.get("q_from")
        q_to = info.get("q_to")

        if q_from is None:
            return raw

        return f"{q_from}_to_{q_to}" if q_to else q_from

    def build_event_dictionary(self):
        """Construye un diccionario uniforme code → label normalizado."""
        if self.dict_events is None:
            self.event_dictionary = {}
            return {}

        event_dict = {}

        for long_label, code in self.dict_events.items():
            code = int(code)
            normalized = self.normalize_label(long_label)
            event_dict[code] = normalized

        self.event_dictionary = event_dict
        return event_dict

    # ======================================================================
    # PIPELINE CLEANING
    # ======================================================================
    def _validate_clean_pipeline(self):
        self.clean_global = load_config(self.root / "clean_pipelines.yml")
        if self.clean_global is None:
            raise RuntimeError("No se pudo cargar clean_pipelines.yml global")

        pipeline_cfg = self.config.get("pipelineCleanData", {})
        self.pipeline_cfg = pipeline_cfg.get("available_functions", [])

        global_funcs = {
            list(item.keys())[0] for item in self.clean_global.get("clean_functions", [])
        }

        for item in self.pipeline_cfg:
            func_name, enabled = list(item.items())[0]
            if enabled and func_name not in global_funcs:
                raise RuntimeError(
                    f"'{func_name}: true' en {self.name} pero no existe en clean_pipelines.yml"
                )

    # ======================================================================
    # CTL-COMPONENTS (TABULAR + EVENTOS)
    # ======================================================================
    def _generate_ctl_components(self):
        ctl_path = self.path / "ctl_components.yml"

        if self.type == "TabularDataSet":
            data = self._build_tabular_components()
        else:
            data = self._build_event_components()

        with open(ctl_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

        self.componentes = data

    def _build_tabular_components(self):
        out = {"components": {}}

        for comp_name in self.components_local.keys():
            g = self.components_global[comp_name]

            out["components"][comp_name] = {
                "name": g.get("name", comp_name),
                "description": g.get("description", ""),
                "measurements": {},
            }

            for meas in self.components_local[comp_name]:
                gm = g["measurements"][meas]
                out["components"][comp_name]["measurements"][meas] = {
                    "display_name": gm.get("display_name", meas),
                    "description": gm.get("description", ""),
                    "type": gm.get("type", ""),
                    "unit": gm.get("unit", ""),
                }

        return out

    def _build_event_components(self):
        out = {"components": {}}
        grouped = {}
        event_dict = self.event_dictionary

        for full_key, code in self.dict_events.items():
            code = int(code)

            info = self.parse_event_name(full_key)
            component = info.get("component") or full_key
            q_to = info.get("q_to")

            # FIX: algunos labels V1 venían con "_from" dentro del componente
            if isinstance(component, str):
                component = component.replace("_from", "")

            base = component
            grouped.setdefault(base, {"raw": [], "from_to": []})

            label = event_dict.get(code, self.normalize_label(full_key))

            if q_to is None:
                grouped[base]["raw"].append((label, code))
            else:
                grouped[base]["from_to"].append((label, code))

        for base, info in grouped.items():
            comp_name = self._infer_component_from_base(base)

            if comp_name not in out["components"]:
                g = self.components_global.get(comp_name, {})
                out["components"][comp_name] = {
                    "name": g.get("name", comp_name),
                    "description": g.get("description", ""),
                    "measurements": {},
                }

            raw_labels = [lbl for lbl, _ in info["raw"]]
            raw_codes = [code for _, code in info["raw"]]

            if raw_labels or raw_codes:
                out["components"][comp_name]["measurements"][f"{base}-raw"] = {
                    "display_name": f"{base}-raw",
                    "description": f"Evento de estado de {base}",
                    "type": "event",
                    "unit": "event",
                    "labels": raw_labels,
                    "encodes": raw_codes,
                }

            ft_labels = [lbl for lbl, _ in info["from_to"]]
            ft_codes = [code for _, code in info["from_to"]]

            if ft_labels or ft_codes:
                out["components"][comp_name]["measurements"][f"{base}-from_to"] = {
                    "display_name": f"{base}-from_to",
                    "description": f"Cambio de estado de {base}",
                    "type": "from_to",
                    "unit": "event-change",
                    "labels": ft_labels,
                    "encodes": ft_codes,
                }

        return out

    def _infer_component_from_base(self, base):
        for comp, gdata in self.components_global.items():
            if base in gdata.get("measurements", {}):
                return comp
        return base.split("_")[0]

    # ======================================================================
    # CSV RAW
    # ======================================================================
    def _load_raw_csv(self):
        """Solo carga CSV, NO toca timestamps."""
        if self.parquet_file.exists():
            return

        raw_dir = self.path / "raw"
        files = glob.glob(str(raw_dir / "*.csv"))

        if not files:
            raise RuntimeError(f"No hay CSV en {raw_dir}")

        dfs = [pd.read_csv(f) for f in files]
        df_raw = pd.concat(dfs, ignore_index=True)

        ts = self.metadata.get("timestamp_col", "Timestamp")
        df_raw = df_raw.dropna(subset=[ts]).sort_values(ts)

        self.df = df_raw.copy()

    # ======================================================================
    # CLEAN PIPELINE → PARQUET
    # ======================================================================
    def _run_clean_pipeline(self):
        if self.parquet_file.exists():
            return

        funcs_global = self.clean_global.get("clean_functions", [])

        for item in self.pipeline_cfg:
            func_name, enabled = list(item.items())[0]
            if not enabled:
                continue

            meta = next(f[func_name] for f in funcs_global if func_name in f)
            module = importlib.import_module(meta["module"])
            func = getattr(module, meta["func"])

            df_out = func(self)
            if df_out is not None:
                self.df = df_out

        self.df.to_parquet(self.parquet_file, index=True)
        logging.info(f"📦 Guardado parquet limpio: {self.parquet_file}")

    # ======================================================================
    # CARGA DF
    # ======================================================================
    def load_df(self):
        df = pd.read_parquet(self.parquet_file)
        return df

