import logging
from pathlib import Path
import json
import yaml
import pandas as pd
import numpy as np
import re
import os

from config_env import settings_env

class SubDataset:
    """
    SubDataset
    ==========
    Wrapper inteligente sobre un parquet externo (MLOps artifact).
    """

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
# --- ATRIBUTOS RESTAURADOS ---
        self.timestamp_col = cfg.get("timestamp_col", settings_env.TIMESTAMP_COL)
        self.merge_on = cfg.get("merge_on", self.timestamp_col)
        self.strategy = cfg.get("strategy")
        # -----------------------------

        # 🔥 MODIFICADO: Crear carpeta principal y darle permisos totales
        # 🔥 MODIFICADO: Crear carpeta principal anulando el umask de Docker
        self.epoch_processed_root = Path(settings_env.EPOCH_PROCESSED_DIR)
        old_umask = os.umask(0) # Anulamos restricciones de permisos
        try:
            self.epoch_processed_root.mkdir(parents=True, exist_ok=True, mode=0o777)
            os.chmod(str(self.epoch_processed_root), 0o777)
        except Exception as e:
            logging.error(f"⚠️ No se pudo dar permisos a la carpeta raíz: {e}")
        finally:
            os.umask(old_umask) # Restauramos la seguridad del sistema siempre
            
        self.components = {}
        self.event_dictionary = {} # Diccionario normalizado code -> label

        if self.type == "tabular":
            self._load_temporal_components()
        else:
            # 1. Primero cargamos el diccionario (Code -> Label)
            self._build_event_dictionary_code_to_label()
            
            # 2. Ahora construimos los componentes basándonos en ese diccionario
            if self.event_dictionary:
                logging.info(f"📘 Diccionario eventos cargado para {self.name} ({len(self.event_dictionary)} eventos)")
                self._load_or_build_epoch_components()
            else:
                logging.warning(f"⚠️ Diccionario vacío para {self.name}. No se generarán columnas de eventos.")

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
        """
        Intenta cargar componentes desde YAML estático, si no existe, 
        los infiere del diccionario de eventos.
        """
        ctl_path = Path(settings_env.CTRL_COMPONENTS_EPOCH)
        if ctl_path.exists():
            with open(ctl_path, "r", encoding="utf-8") as f:
                self.components = yaml.safe_load(f).get("components", {})
            return

        # Si no hay YAML, construimos dinámicamente
        self.components = self._build_epoch_components_from_dictionary()
        logging.info(f"🔧 Componentes generados dinámicamente para {self.name}: {list(self.components.keys())}")

    def _load_event_dictionary(self) -> dict:
        """
        Carga el diccionario JSON específico.
        """
        # 1. PRIORIDAD: Archivo específico de la versión
        # dict_path = self.parquet_path.parent / "02_prepareeventsds_params.json"
        dict_path = self.parquet_path.parent / settings_env.CTRL_COMPONENTS_EPOCH_DICTIONARY
        
        # 2. FALLBACK: Variable de entorno
        if not dict_path.exists():
            dict_path = self.parquet_path.parent / settings_env.CTRL_COMPONENTS_EPOCH_DICTIONARY
        
        if not dict_path.exists():
            logging.warning(f"⚠️ No se encontró diccionario de eventos en {self.parquet_path.parent}")
            return {}

        try:
            with open(dict_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"❌ Error leyendo JSON {dict_path}: {e}")
            return {}

    def _build_event_dictionary_code_to_label(self):
        """
        Invierte el diccionario: { "Label": 1 } -> { 1: "Label" }
        Maneja enteros y listas.
        """
        raw_dict = self._load_event_dictionary()
        event_dict = {}

        for label_desc, code_or_list in raw_dict.items():
            if isinstance(code_or_list, list):
                codes = code_or_list
            else:
                codes = [code_or_list]

            for c in codes:
                try:
                    code_val = int(c)
                    event_dict[code_val] = label_desc
                except (ValueError, TypeError):
                    continue

        self.event_dictionary = event_dict

    def _build_epoch_components_from_dictionary(self):
        """
        Genera componentes agrupando códigos.
        
        MEJORA: Recupera el TIPO original (potencia, voltaje) del YAML temporal
        para las columnas de estado, manteniendo 'from_to' para las transiciones.
        """
        
        # -----------------------------------------------------------
        # 1. Crear Mapas: 
        #    - Medida -> Componente ID (Padre)
        #    - Medida -> Tipo Original (potencia, voltaje...)
        # -----------------------------------------------------------
        measure_to_group_map = {}
        measure_to_type_map = {} # Nuevo mapa de tipos
        
        ctl_path = Path(settings_env.CTRL_COMPONENTS_TEMPORAL)
        
        if ctl_path.exists():
            try:
                with open(ctl_path, "r", encoding="utf-8") as f:
                    temp_comps = yaml.safe_load(f).get("components", {})
                    for comp_id, comp_data in temp_comps.items():
                        for measure_name, m_data in comp_data.get("measurements", {}).items():
                            measure_to_group_map[measure_name] = comp_id
                            # Guardamos el tipo original (ej: "potencia")
                            measure_to_type_map[measure_name] = m_data.get("type", "state")
            except Exception as e:
                logging.warning(f"⚠️ No se pudo leer mapa temporal: {e}")

        # -----------------------------------------------------------
        # 2. Agrupar códigos por nombre de columna
        # -----------------------------------------------------------
        grouped = {}
        state_suffix_pattern = re.compile(r'_([0-9\.]+|NaN)_([0-9\.]+|NaN)$')

        for code, label in self.event_dictionary.items():
            is_transition = "-to-" in label
            
            if is_transition:
                base_part = label.split("-to-")[0]
            else:
                base_part = label

            match = state_suffix_pattern.search(base_part)
            if match:
                clean_name = base_part[:match.start()].strip("_")
            else:
                clean_name = base_part.strip("_")

            col_name = f"{clean_name}-from_to" if is_transition else clean_name

            if col_name not in grouped:
                grouped[col_name] = []
            grouped[col_name].append(code)

        # -----------------------------------------------------------
        # 3. Construir Componentes
        # -----------------------------------------------------------
        components = {}
        
        for col_name, codes_list in grouped.items():
            search_key = col_name.replace("-from_to", "")
            
            # Asignar grupo padre
            group_id = measure_to_group_map.get(search_key, search_key)
            
            if group_id not in components:
                components[group_id] = {
                    "name": group_id,
                    "measurements": {}
                }
            
            # LÓGICA DE TIPOS CORREGIDA:
            if "-from_to" in col_name:
                final_type = "from_to"
                display_suffix = "Transitions"
            else:
                # Si es estado, recuperar el tipo original (potencia, voltaje, etc.)
                final_type = measure_to_type_map.get(search_key, "state")
                display_suffix = "States"
            
            # Añadir medida con el tipo correcto
            components[group_id]["measurements"][col_name] = {
                "type": final_type, 
                "encodes": sorted(list(set(codes_list))),
                "display_name": display_suffix
            }

        logging.info(f"🔧 Componentes agrupados: {list(components.keys())}")
        return components

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

        if not event_col:
            logging.error(f"❌ No se encontró columna de eventos raw en {self.name}.")
            return pd.DataFrame()

        ts_col = self.timestamp_col
        df_subset = df[[ts_col, event_col]].dropna()

        if df_subset.empty:
             logging.warning(f"⚠️ DF vacío tras limpiar NAs en {self.name}.")
             return pd.DataFrame()

        df_subset = df_subset.sort_values(ts_col)

        out = df_subset.groupby(ts_col)[event_col].apply(list).reset_index()
        out.columns = [ts_col, "codes"]

        # Crear columnas dinámicas
        ft_map = {}
        for comp_data in self.components.values():
            for m_name, m_data in comp_data.get("measurements", {}).items():
                codes = m_data.get("encodes", [])
                if codes:
                    ft_map[m_name] = set(codes)

        if not ft_map:
            logging.warning(f"⚠️ No se generaron componentes para {self.name}.")

        for col_name, code_set in ft_map.items():
            out[col_name] = out["codes"].apply(lambda arr, s=code_set: self._first_code_in_set(arr, s))

        logging.info(f"✅ Procesados {len(out)} registros de eventos para {self.name}.")
        return out.drop(columns=["codes"])

    def load_or_process_epoch(self) -> pd.DataFrame:
        out_path = self.epoch_processed_root / self.name / self.parquet_path.name
        
        # 🔥 1. Crear subcarpeta anulando el umask temporalmente
        old_umask = os.umask(0)
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True, mode=0o777)
            os.chmod(str(out_path.parent), 0o777)
        except Exception as e: 
            logging.error(f"⚠️ Error dando permisos a subcarpeta {out_path.parent}: {e}")
        finally:
            os.umask(old_umask)

        if out_path.exists(): 
            return pd.read_parquet(out_path)

        logging.info(f"⚙️ Procesando eventos para {self.name}...")
        df_raw = self.load_df()
        
        if df_raw.empty: return pd.DataFrame()

        df_processed = self._process_epoch_df(df_raw)

        if not df_processed.empty:
            # 🔥 2. Guardado atómico con permisos forzados
            tmp_path = out_path.with_suffix('.parquet.tmp')
            
            old_umask_file = os.umask(0)
            try:
                # Escribir el tmp
                df_processed.to_parquet(tmp_path, index=False)
                
                # Permisos al tmp (666)
                os.chmod(str(tmp_path), 0o666)
                
                # Renombrar (conserva los permisos)
                os.rename(str(tmp_path), str(out_path))
                
                # Por si acaso, re-aplicar permisos al final
                os.chmod(str(out_path), 0o666)
            except Exception as e:
                logging.error(f"⚠️ Error dando permisos al archivo parquet: {e}")
            finally:
                os.umask(old_umask_file)
        
        return df_processed