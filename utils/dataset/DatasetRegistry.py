# utils/dataset/DatasetRegistry.py
import logging
from pathlib import Path
import yaml

from utils.dataset.SubDataset import SubDataset
from utils.dataset.DatasetComposite import DatasetComposite
from debug.debug import save_debug_info


class DatasetRegistry:
    """
    DatasetRegistry:
      ✓ Carga control.yml general
      ✓ Crea SubDatasets (los cuales generan parquet si no existe)
      ✓ Crea DatasetComposite (los cuales generan parquet si no existe)
      ✓ NO carga DataFrames en memoria.
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        self.control_general = self.root / "control.yml"

        if not self.control_general.exists():
            raise RuntimeError(f"No existe control.yml en {self.root}")

        with open(self.control_general, "r", encoding="utf-8") as f:
            self.control = yaml.safe_load(f)

        # ---------------------------------------------------------
        # Cargar SubDatasets (tabular + event-encoded)
        # ---------------------------------------------------------
        self.subdatasets = self._load_subdatasets()

        # ---------------------------------------------------------
        # Cargar composites
        # ---------------------------------------------------------
        self.datasets = self._load_datasets()


    # ======================================================================
    #   CARGA SUBDATASETS
    # ======================================================================
    def _load_subdatasets(self):
        out = {}
        section = self.control.get("subdatasets", {})

        logging.info("📁 Cargando subdatasets declarados en control.yml")

        for name, cfg in section.items():

            logging.info(f"   → SubDataset: {name}")

            # Crea SubDataset → este ejecuta pipeline y genera parquet si no existe.
            out[name] = SubDataset(
                name=name,
                root=self.root,
                cfg=cfg
            )

        return out

    # ======================================================================
    #   CARGA DATASETS COMPLETOS
    # ======================================================================
    def _load_datasets(self):
        out = {}
        section = self.control.get("Datasets", {})

        logging.info("📦 Cargando Datasets Compuestos (DatasetComposite)")

        for ds_name, cfg in section.items():
            sub_cfg = cfg.get("subdatasets", {})

            main = sub_cfg.get("main")
            if main is None:
                raise ValueError(
                    f"Dataset '{ds_name}' no define subdataset 'main' en control.yml"
                )

            logging.info(f"   → DatasetComposite '{ds_name}' (main = {main})")

            # Crea DatasetComposite (generará parquet si no existe)
            out[ds_name] = DatasetComposite(
                name=ds_name,
                registry=self,
                subdatasets=sub_cfg
            )

        return out

    # ======================================================================
    #   API PÚBLICA
    # ======================================================================
    def list(self):
        """Devuelve lista de nombres de datasets disponibles."""
        return list(self.datasets.keys())

    def get(self, name):
        """Devuelve un DatasetComposite por nombre."""
        if name not in self.datasets:
            raise KeyError(f"El dataset '{name}' no existe.")
        return self.datasets[name]

    def get_default(self):
        """Devuelve dataset por defecto de control.yml."""
        default = self.control.get("default_dataset")
        if not default:
            raise RuntimeError("control.yml no define 'default_dataset'.")
        return self.get(default)
