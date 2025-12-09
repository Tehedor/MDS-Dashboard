# utils/dataset/SubDataset.py
import logging
from pathlib import Path
import pandas as pd
import yaml
import importlib
import glob

from utils.helpers import load_config
from debug.debug import save_debug_info


class SubDataset:
    """
    SubDataset:
      - TabularDataSet
      - EventEncodedDataSet

    Funcionalidades:
      ✓ Carga config local
      ✓ Validación de componentes
      ✓ Carga de dictionary (eventos)
      ✓ Validación de clean_pipelines
      ✓ Generación automática de ctl_components.yml
      ✓ Ejecución del pipeline de limpieza → parquet final
      ✓ Carga del parquet a self.df
    """

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
        # Crear folder processed y parquet final
        # ---------------------------------------------------------
        self.processed_dir = self.path / "processed"
        self.processed_dir.mkdir(exist_ok=True, parents=True)
        self.parquet_file = self.processed_dir / f"{self.name}.parquet"

        # ---------------------------------------------------------
        # Carga de componentes
        # ---------------------------------------------------------
        self._load_components()
        self._validate_components()

        # ---------------------------------------------------------
        # Si es EventEncoded → cargar dictionary
        # ---------------------------------------------------------
        self._load_dictionary()

        # ---------------------------------------------------------
        # Validación de pipeline
        # ---------------------------------------------------------
        self._validate_clean_pipeline()

        # ---------------------------------------------------------
        # Generar archivo ctl_components.yml
        # ---------------------------------------------------------
        self._generate_ctl_components()

        # ---------------------------------------------------------
        # Ejecutar pipeline de limpieza → generar parquet si no existe
        # ---------------------------------------------------------
                # ---------------------------------------------------------
        # Cargar y unir CSV del subdataset
        # ---------------------------------------------------------
        if not self.parquet_file.exists():
            self._load_raw_csv()
            self._run_clean_pipeline()
        else:
            logging.info(f"📦 Parquet ya existe para {self.name}, no se limpia.")
        # ---------------------------------------------------------
        # Cargar DataFrame limpio en memoria
        # ---------------------------------------------------------
        self._load_dataframe()

        # ---------------------------------------------------------
        # DEBUG opcional
        # ---------------------------------------------------------
        # save_debug_info(
        #     {
        #         "name": self.name,
        #         "metadata": self.metadata,
        #         "components_local": self.components_local,
        #         "components_global_keys": list(self.components_global.keys()),
        #         "pipeline_cfg": self.config.get("pipelineCleanData"),
        #         "dict_events_keys": list(self.dict_events.keys())
        #         if self.dict_events
        #         else None,
        #     },
        #     filename=f"debug_{self.name}_config",
        # )

    # ======================================================================
    #       CARGA DE COMPONENTES
    # ======================================================================
    def _load_components(self):
        global_components = load_config(self.root / "components.yml")
        if global_components is None:
            raise RuntimeError("No se pudo cargar components.yml global")

        self.components_global = global_components.get("components", {})
        self.timestamps_global = global_components.get("timestamps", {})

        # TABULAR requiere components locales
        if self.type == "TabularDataSet":
            local_components = self.config.get("components")
            if local_components is None:
                raise RuntimeError(
                    f"El subdataset '{self.name}' es Tabular pero NO define 'components:'"
                )
            self.components_local = local_components

        else:
            # EventEncoded NO define components locales
            self.components_local = None

    def _validate_components(self):
        """Tabular → validar que sus componentes existan en components.yml global."""
        if self.type != "TabularDataSet":
            return True

        for comp_name in self.components_local.keys():
            if comp_name not in self.components_global:
                raise RuntimeError(
                    f"El subdataset '{self.name}' declara componente '{comp_name}' "
                    f"pero NO existe en components.yml global"
                )
        return True

    # ======================================================================
    #       CARGA DICCIONARIO EVENTOS
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

    # ======================================================================
    #       VALIDACIÓN PIPELINE LIMPIEZA
    # ======================================================================
    def _validate_clean_pipeline(self):
        self.clean_global = load_config(self.root / "clean_pipelines.yml")
        if self.clean_global is None:
            raise RuntimeError("No se pudo cargar clean_pipelines.yml global")

        pipeline_cfg = self.config.get("pipelineCleanData", {})
        self.pipeline_cfg = pipeline_cfg.get("available_functions", [])

        # funciones globales disponibles
        global_funcs = {
            list(item.keys())[0] for item in self.clean_global.get("clean_functions", [])
        }

        # validar llamadas
        for item in self.pipeline_cfg:
            func_name, enabled = list(item.items())[0]
            if enabled and func_name not in global_funcs:
                raise RuntimeError(
                    f"En '{self.name}' → '{func_name}: true' pero NO existe en clean_pipelines.yml global"
                )

    # ======================================================================
    #       GENERACIÓN ARCHIVO CTL COMPONENTS
    # ======================================================================
    def _generate_ctl_components(self):
        ctl_path = self.path / "ctl_components.yml"

        if self.type == "TabularDataSet":
            data = self._build_tabular_components()
        else:
            data = self._build_event_components()

        with open(ctl_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                data, f, sort_keys=False, default_flow_style=False, allow_unicode=True
            )

        self.componentes = data  # almacenar inline para DatasetComposite

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
                if meas not in g["measurements"]:
                    raise RuntimeError(
                        f"La medida '{meas}' declarada en {self.name} NO existe globalmente."
                    )

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

        for key, code in self.dict_events.items():
            if "_from_" in key:
                base = key.split("_from_")[0]
                grouped.setdefault(base, {"raw": [], "from_to": []})
                grouped[base]["from_to"].append((key, code))
            else:
                base = key.split("_Q")[0]
                grouped.setdefault(base, {"raw": [], "from_to": []})
                grouped[base]["raw"].append((key, code))

        for base_name, blocks in grouped.items():

            comp_name = self._infer_component_from_base(base_name)

            if comp_name not in out["components"]:
                g = self.components_global.get(comp_name, {})
                out["components"][comp_name] = {
                    "name": g.get("name", comp_name),
                    "description": g.get("description", ""),
                    "measurements": {},
                }

            # RAW
            labels_raw = [k.split(base_name + "_")[1] for k, _ in blocks["raw"]]
            enc_raw = [c for _, c in blocks["raw"]]

            out["components"][comp_name]["measurements"][f"{base_name}-raw"] = {
                "display_name": f"{base_name}-raw",
                "description": f"Evento de estado de {base_name}",
                "type": "event",
                "unit": "event",
                "labels": labels_raw,
                "encodes": enc_raw,
            }

            # FROM-TO
            labels_ft = [k.split(base_name + "_")[1] for k, _ in blocks["from_to"]]
            enc_ft = [c for _, c in blocks["from_to"]]

            out["components"][comp_name]["measurements"][f"{base_name}-from_to"] = {
                "display_name": f"{base_name}-from_to",
                "description": f"Evento de cambio de estado de {base_name}",
                "type": "from_to",
                "unit": "event-change",
                "labels": labels_ft,
                "encodes": enc_ft,
            }

        return out

    def _infer_component_from_base(self, base_name: str):
        for comp, gdata in self.components_global.items():
            if base_name in gdata.get("measurements", {}):
                return comp

        return base_name.split("_")[0]


    # ======================================================================
    #       CARGA Y MERGE AUTOMÁTICO DE CSV DEL SUBDATASET
    # ======================================================================
    def _load_raw_csv(self):
        """
        Detecta automáticamente todos los CSV ubicados en la carpeta 'raw/'
        dentro del dataset, los concatena y genera self.raw_df y self.df.
        """
        if self.parquet_file.exists():
            # logging.info(f"📦 Parquet ya existe para {self.name}, no se limpia.")
            return

        raw_dir = self.path / "raw"

        if not raw_dir.exists():
            raise RuntimeError(
                f"El dataset '{self.name}' no contiene carpeta 'raw/' con archivos CSV."
            )

        # buscar todos los csv
        pattern = str(raw_dir / "*.csv")
        file_list = glob.glob(pattern)

        if not file_list:
            raise RuntimeError(
                f"No se encontraron CSV dentro de {raw_dir}"
            )

        logging.info(f"📄 [{self.name}] Cargando {len(file_list)} archivos de raw/")

        dfs = []
        for fp in file_list:
            df_piece = pd.read_csv(fp)
            dfs.append(df_piece)
            logging.info(f"   ✔ Cargado: {Path(fp).name} ({len(df_piece)} filas)")

        df_raw = pd.concat(dfs, ignore_index=True)

        # Convertir timestamp
        ts_col = self.metadata.get("timestamp_col", "Timestamp")

        if ts_col not in df_raw.columns:
            raise RuntimeError(
                f"El dataset '{self.name}' no contiene columna timestamp '{ts_col}'"
            )

        df_raw[ts_col] = pd.to_datetime(df_raw[ts_col], errors="coerce")
        df_raw = df_raw.dropna(subset=[ts_col]).sort_values(ts_col)

        self.raw_df = df_raw
        self.df = df_raw.copy()

        logging.info(
            f"📦 [{self.name}] Dataset unificado: {len(self.df)} filas, {len(self.df.columns)} columnas"
        )


    # ======================================================================
    #       PIPELINE DE LIMPIEZA → GENERA PARQUET
    # ======================================================================
    def _run_clean_pipeline(self):
        """Ejecuta las funciones del pipeline si el parquet no existe."""

        if self.parquet_file.exists():
            # logging.info(f"📦 Parquet ya existe para {self.name}, no se limpia.")
            return

        funcs_global = self.clean_global.get("clean_functions", [])
        df = None

        for item in self.pipeline_cfg:
            func_name, enabled = list(item.items())[0]
            if not enabled:
                continue

            meta = next((f[func_name] for f in funcs_global if func_name in f), None)
            if meta is None:
                raise RuntimeError(f"No se encontró metadata para '{func_name}'")

            module = importlib.import_module(meta["module"])
            func = getattr(module, meta["func"])

            logging.info(f"🧼 Ejecutando limpieza: {func_name}")

            # Todas las funciones operan como func(self)
            df = func(self)

            # permitir que func devuelva df o lo coloque en self.df
            if df is not None:
                self.df = df

        # asegurarse que hay df
        if not hasattr(self, "df"):
            raise RuntimeError(f"La pipeline de '{self.name}' no generó dataframe")

        # guardar parquet final
        self.df.to_parquet(self.parquet_file, index=True)
        logging.info(f"📦 Guardado parquet limpio: {self.parquet_file}")

    # ======================================================================
    #       CARGA DEL PARQUET
    # ======================================================================
    def _load_dataframe(self):
        if not self.parquet_file.exists():
            raise RuntimeError(f"No existe parquet del subdataset {self.name}")

        self.df = pd.read_parquet(self.parquet_file)
