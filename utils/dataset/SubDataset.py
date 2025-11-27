# utils/dataset/dataset.py
from pathlib import Path
import pandas as pd
from utils.helpers import load_config
from .loader import load_or_build_parquet

class SubDataset:

    def __init__(self, name: str, root: Path, cfg: dict):
        self.name = name
        self.cfg = cfg

        # tipo: "tabular" o "event-encoded"
        self.type = cfg.get("type")

        # ruta base del subdataset
        self.path = root / cfg.get("path")

        # archivo de control YML dentro del subdataset
        self.control_file = self.path / cfg.get("control_file")

        # 👉 FIX: definir control_path para compatibilidad con loader
        self.control_path = self.control_file

        # nombre de columna timestamp
        self.timestamp_col = cfg.get("timestamp_col", "Timestamp")

        # cargar config YAML del propio subdataset (control_dataset.yml)
        self.config = load_config(self.control_file)

        # rutas de directorios
        self.raw_dir = self.path / "raw"
        self.processed_dir = self.path / "processed"
        self.processed_dir.mkdir(exist_ok=True, parents=True)

        # salida parquet
        self.parquet_file = self.processed_dir / f"{name}.parquet"

        # lanzar construcción de parquet si no existe
        load_or_build_parquet(self)

        # cargar dataframe
        self.df = pd.read_parquet(self.parquet_file)

    def info(self):
        return {
            "name": self.name,
            "rows": len(self.df),
            "cols": list(self.df.columns)
        }
