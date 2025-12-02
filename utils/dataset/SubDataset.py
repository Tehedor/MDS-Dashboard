# utils/dataset/dataset.py
from json import load
from pathlib import Path
import pandas as pd
from utils.helpers import load_config
from .loader import load_or_build_parquet
from debug.debug import save_debug_info

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
        # self.control_path = self.control_file

        # nombre de columna timestamp
        self.timestamp_col = cfg.get("timestamp_col", "Timestamp")

        # cargar config YAML del propio subdataset (control_dataset.yml)
        self.config = load_config(self.control_file)
        
        
        metadata = self.config.get("metadata", {})
        comp_name = metadata.get("components")
        components_path = self.path / comp_name if comp_name else None
        # rutas de directorios
        self.componentes = load_config(components_path)
        # save_debug_info(content_source=self.componentes, filename=f"1debug_{self.name}_componentes.txt", head=f"# componentes of subdataset {self.name}")
        if self.componentes is None:
            raise ValueError(f"El subdataset '{name}' no tiene la sección 'metadata/componentes' en su control_file")
        
        
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
            "cols": list(self.df.columns),
            "componentes": self.componentes,
        }


    # ============================================================
    #   TABULAR COLUMNS
    # ============================================================
    def get_tabular_columns(self):
        """
        Devuelve una lista de columnas tabulares con metadatos mínimos:
        - name
        - type = 'tabular'
        - component = None
        """
        if self.type != "tabular":
            return []

        cols = []
        for col in self.df.columns:
            if col == self.timestamp_col:
                continue
            cols.append({
                "name": col,
                "type": "tabular",
                "component": None
            })

        save_debug_info(content_source=cols, filename=f"debug_{self.name}_tabular_columns.txt", head=f"# tabular columns of subdataset {self.name}")
        return cols

    # ============================================================
    #   EVENT COLUMNS (via YAML)
    # ============================================================
    def get_event_columns(self):
        """
        Lee el YAML de componentes y devuelve una lista de:
        {
            "component": "Battery",
            "measurement": "Battery_Active_Power",
            "type": "raw" | "from_to",
            "codes": [...],
            "id": "Battery_Active_Power_raw"
        }
        """
        if self.type != "event-encoded":
            return []

        out = []

        components_cfg = self.componentes.get("components", {})

        for component_name, comp_data in components_cfg.items():

            measurements = comp_data.get("measurements", {})
            for meas_key, meas_obj in measurements.items():

                meas_name = meas_obj.get("name", meas_key)
                meas_block = meas_obj.get("measurements", {})

                for block_key, block_data in meas_block.items():

                    if block_key.endswith("-raw"):
                        mtype = "raw"
                    elif block_key.endswith("-from_to"):
                        mtype = "from_to"
                    else:
                        continue

                    encoded = block_data.get("columns_encoded", [])

                    out.append({
                        "component": component_name,
                        "measurement": meas_name,
                        "type": mtype,
                        "codes": encoded,
                        "id": f"{meas_name}_{mtype}"
                    })

        save_debug_info(content_source=out, filename=f"debug_{self.name}_event_columns.txt", head=f"# event columns of subdataset {self.name}")
        return out
