import logging
from pathlib import Path
import yaml

from utils.dataset.SubDataset import SubDataset
from utils.dataset.DatasetComposite import DatasetComposite

class DatasetRegistry:

    def __init__(self, root: Path):
        self.root = Path(root)
        self.control_general = self.root / "control.yml"

        if not self.control_general.exists():
            raise RuntimeError(f"No existe control.yml en {self.root}")

        with open(self.control_general, "r", encoding="utf-8") as f:
            self.control = yaml.safe_load(f)
            
        self.subdatasets = self._load_subdatasets()
        self.datasets = self._load_datasets()

    # -------------------------------------------------------------
    def _load_subdatasets(self):
        out = {}
        section = self.control.get("subdatasets", {})

        logging.debug("Cargando subdatasets: %s", list(section.items()))
        logging.debug("sdasdasdas")
        logging.debug("sdasdasdas")
        for name, cfg in section.items():
            out[name] = SubDataset(
                name=name,
                root=self.root,
                cfg=cfg
            )

        return out

    # -------------------------------------------------------------
    def _load_datasets(self):
        out = {}
        section = self.control.get("Datasets", {})

        for ds_name, cfg in section.items():
            sub_cfg = cfg.get("subdatasets", {})
            main = sub_cfg.get("main")

            if main is None:
                raise ValueError(f"Dataset '{ds_name}' no tiene subdataset 'main' definido")

            out[ds_name] = DatasetComposite(
                name=ds_name,
                registry=self,
                subdatasets=sub_cfg
            )

        return out

    # -------------------------------------------------------------
    def list(self):
        return list(self.datasets.keys())

    def get(self, name):
        return self.datasets[name]

    def get_default(self):
        default = self.control.get("default_dataset")
        return self.datasets[default]
    
