# utils/dataset/DatasetRegistry.py
import logging
from pathlib import Path
import yaml

from utils.dataset.SubDataset import SubDataset
from utils.dataset.DatasetComposite import DatasetComposite


class DatasetRegistry:
    """
    DatasetRegistry
    ===============
    Catálogo de datasets definido por control.yml.

    Responsabilidades:
      - Leer control.yml
      - Crear SubDatasets
      - Crear DatasetComposite
      - Exponer datasets disponibles

    ❌ NO carga parquets
    ❌ NO procesa datos
    ❌ NO ejecuta pipelines
    """

    # --------------------------------------------------
    # INIT
    # --------------------------------------------------
    def __init__(self, root: Path):
        self.root = Path(root)

        self.control_path = self.root / "control.yml"
        if not self.control_path.exists():
            raise RuntimeError(
                f"No existe control.yml en {self.control_path}"
            )

        # ------------------------------
        # Leer control.yml
        # ------------------------------
        with open(self.control_path, "r", encoding="utf-8") as f:
            self.control = yaml.safe_load(f)

        logging.info("📘 control.yml cargado correctamente")

        # ------------------------------
        # SubDatasets
        # ------------------------------
        self.subdatasets = self._load_subdatasets()

        # ------------------------------
        # Datasets (Composite)
        # ------------------------------
        self.datasets = self._load_datasets()

        # ------------------------------
        # Default
        # ------------------------------
        self.default_dataset = self.control.get("default_dataset")
        if self.default_dataset not in self.datasets:
            if self.datasets:
                self.default_dataset = next(iter(self.datasets))
                logging.warning(
                    "default_dataset no existe en Datasets; usando '%s'",
                    self.default_dataset,
                )
            else:
                self.default_dataset = None
                logging.warning(
                    "control.yml no contiene Datasets utilizables; la app arrancará sin dataset por defecto"
                )

        logging.info(
            f"📦 Dataset por defecto: {self.default_dataset}"
        )

    # --------------------------------------------------
    # SUBDATASETS
    # --------------------------------------------------
    def _load_subdatasets(self):
        out = {}

        section = self.control.get("subdatasets", {})
        if not section:
            logging.warning("control.yml no define 'subdatasets'")
            return out

        logging.info("📁 Cargando SubDatasets")

        for name, cfg in section.items():
            logging.info(f"   → SubDataset '{name}'")

            out[name] = SubDataset(
                name=name,
                root=self.root,
                cfg=cfg
            )

        return out

    # --------------------------------------------------
    # DATASETS (COMPOSITE)
    # --------------------------------------------------
    def _load_datasets(self):
        out = {}

        section = self.control.get("Datasets", {})
        if not section:
            logging.warning("control.yml no define 'Datasets'")
            return out

        logging.info("📦 Cargando DatasetComposite")

        for name, cfg in section.items():
            sub_cfg = cfg.get("subdatasets")
            if not sub_cfg:
                raise RuntimeError(
                    f"Dataset '{name}' no define 'subdatasets'"
                )

            out[name] = DatasetComposite(
                name=name,
                registry=self,
                subdatasets=sub_cfg
            )

        return out

    # --------------------------------------------------
    # API PUBLICA
    # --------------------------------------------------
    def list(self):
        """Lista de nombres de DatasetComposite disponibles."""
        return list(self.datasets.keys())

    def get(self, name):
        """Obtiene un DatasetComposite por nombre."""
        if name not in self.datasets:
            raise KeyError(
                f"Dataset '{name}' no existe"
            )
        return self.datasets[name]

    def get_default(self):
        """Obtiene el DatasetComposite por defecto."""
        return self.get(self.default_dataset)
