import logging
from pathlib import Path
import json
import yaml
import pandas as pd
import numpy as np
import re

from config_env import settings_env

class SubDataset:
    """
    SubDataset
    ==========
    Wrapper inteligente sobre un parquet externo (MLOps artifact).
    """

    # Regex para capturar componentes y estados Q (ej: MG_Bus_Q05_to_Q10)
    EVENT_REGEX = re.compile(
        r'^(?P<component>.+?)_'
        r'(?P<q_from>Q[0-9]+)'
        r'(?:_to_(?P<q_to>Q[0-9]+))?$'
    )

    def __init__(self, name: str, root: Path, cfg: dict):
        self.name = name
        self.root = root
        self.cfg = cfg
        self.type = cfg.get("type")
        
        if self.type not in ("tabular", "event-encoded"):
            raise RuntimeError(f"SubDataset '{name}': tipo inválido '{self.type}'")

        parquet_path = cfg.get("path")
        if parquet_path is None:
            raise RuntimeError(f"SubDataset '{name}' no define 'path'")
        self.parquet_path = Path(parquet_path)

        # --- ATRIBUTOS RESTAURADOS ---
        self.timestamp_col = cfg.get("timestamp_col", settings_env.TIMESTAMP_COL)
        self.merge_on = cfg.get("merge_on", self.timestamp_col)
        self.strategy = cfg.get("strategy")
        # -----------------------------

        self.epoch_processed_root = Path(settings_env.EPOCH_PROCESSED_DIR)
        self.epoch_processed_root.mkdir(parents=True, exist_ok=True)

        self.components = {}
        self.event_dictionary = {} # Diccionario normalizado code -> label

        if self.type == "tabular":
            self._load_temporal_components()
        else:
            self._load_or_build_epoch_components()
            self._build_event_dictionary_code_to_label()
            logging.info(f"📘 Diccionario eventos cargado para {self.name}")

        logging.info(f"📦 SubDataset '{self.name}' cargado")

    def load_df(self) -> pd.DataFrame:
        df = pd.read_parquet(self.parquet_path)
        ts_col = self.timestamp_col
        if ts_col in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df[ts_col]):
                df[ts_col] = pd.to_datetime(df[ts_col], unit="s", errors="coerce")
            df = df.sort_values(ts_col)
        return df

    def _load_temporal_components(self):
        ctl_path = Path(settings_env.CTRL_COMPONENTS_TEMPORAL)
        if not ctl_path.exists(): return
        with open(ctl_path, "r", encoding="utf-8") as f:
            self.components = yaml.safe_load(f).get("components", {})

    def _load_or_build_epoch_components(self):
        ctl_path = Path(settings_env.CTRL_COMPONENTS_EPOCH)
        if ctl_path.exists():
            with open(ctl_path, "r", encoding="utf-8") as f:
                self.components = yaml.safe_load(f).get("components", {})
            return
        self.components = self._build_epoch_components_from_dictionary()

    def _load_event_dictionary(self) -> dict:
        dict_path = Path(settings_env.CTRL_COMPONENTS_EPOCH_DICTIONARY)
        with open(dict_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_event_dictionary_code_to_label(self):
        raw_dict = self._load_event_dictionary()
        event_dict = {}
        for long_label, code in raw_dict.items():
            try:
                code_val = int(code)
                match = self.EVENT_REGEX.match(long_label)
                if match:
                    gd = match.groupdict()
                    q_f, q_t = gd.get("q_from"), gd.get("q_to")
                    normalized = f"{q_f}_to_{q_t}" if q_t else q_f
                else:
                    normalized = long_label
                event_dict[code_val] = normalized
            except: continue
        self.event_dictionary = event_dict

    @staticmethod
    def _first_code_in_set(arr, code_set):
        if arr is None: return None
        flat = []
        for v in arr:
            if isinstance(v, (list, tuple, np.ndarray)): flat.extend(list(v))
            elif hasattr(v, "item"): flat.append(v.item())
            else: flat.append(v)
        for c in flat:
            try:
                ci = int(c)
                if ci in code_set: return ci
            except: continue
        return None

    def _process_epoch_df(self, df: pd.DataFrame) -> pd.DataFrame:
        event_col = next((c for c in settings_env.EPOCH_EVENT_COLS + ["events"] if c in df.columns), None)
        ts_col = self.timestamp_col
        df = df[[ts_col, event_col]].dropna().sort_values(ts_col)
        
        # Agrupar por timestamp para manejar eventos simultáneos
        out = df.groupby(ts_col)[event_col].apply(list).reset_index()
        out.columns = [ts_col, "codes"]

        ft_map = {}
        for comp in self.components.values():
            for mname, mdata in comp.get("measurements", {}).items():
                if mdata.get("type") == "from_to":
                    ft_map[mname] = set(mdata.get("encodes", []))

        for name, code_set in ft_map.items():
            out[name] = out["codes"].apply(lambda arr, s=code_set: self._first_code_in_set(arr, s))
        
        return out.drop(columns=["codes"])

    def load_or_process_epoch(self) -> pd.DataFrame:
        out_path = self.epoch_processed_root / self.name / self.parquet_path.name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists(): return pd.read_parquet(out_path)
        df_raw = self.load_df()
        df_processed = self._process_epoch_df(df_raw)
        df_processed.to_parquet(out_path, index=False)
        return df_processed