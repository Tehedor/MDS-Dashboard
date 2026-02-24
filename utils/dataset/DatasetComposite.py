# utils/dataset/DatasetComposite.py
import logging
import pandas as pd
import multiprocessing
import os

from config_env import settings_env

# 🔥 VARIABLE GLOBAL: Guarda el proceso vivo para poder fulminarlo
global_epoch_process = None

# 🔥 NUEVA FUNCIÓN: Accesible desde app.py para limpiar la RAM en cualquier momento
# 🔥 NUEVA FUNCIÓN: Accesible desde app.py para limpiar la RAM en cualquier momento
def cancel_background_processing():
    global global_epoch_process
    if global_epoch_process is not None:
        try:
            if global_epoch_process.is_alive():
                logging.warning("🛑 Interrumpiendo proceso de Epoch en segundo plano para liberar RAM...")
                
                # Usamos kill() que es inmediato a nivel de Sistema Operativo
                if hasattr(global_epoch_process, 'kill'):
                    global_epoch_process.kill() 
                else:
                    global_epoch_process.terminate()
                
                # ❌ ELIMINAMOS EL .join() PARA EVITAR DEADLOCKS Y CONGELAMIENTOS EN DASH
                
        except Exception as e:
            logging.error(f"⚠️ Error al intentar matar el proceso en segundo plano: {e}")
        finally:
            # Sea como sea, olvidamos el proceso para que la app pueda continuar
            global_epoch_process = None

class DatasetComposite:
    def __init__(self, name, registry, subdatasets):
        self.name = name
        self.registry = registry
        self.subdatasets_cfg = subdatasets

        main_name = subdatasets.get("main")
        if main_name is None: raise RuntimeError(f"Dataset '{name}' no define subdataset 'main'")

        self.main = registry.subdatasets.get(main_name)
        if self.main is None: raise RuntimeError(f"Dataset '{name}': subdataset main '{main_name}' no existe")

        self.epoch = None
        epoch_name = subdatasets.get("epoch")
        if epoch_name:
            self.epoch = registry.subdatasets.get(epoch_name)
            if self.epoch is None: raise RuntimeError(f"Dataset '{name}': subdataset epoch '{epoch_name}' no existe")

        logging.info(f"🧩 DatasetComposite '{self.name}' (main={main_name}, epoch={epoch_name})")

    def load_for_visualization(self, allow_async=False) -> pd.DataFrame:
        # 1. TABULAR
        df_main = self.main.load_df()

        if not settings_env.EPOCH_MODE:
            if self.epoch is not None:
                self.epoch.load_or_process_epoch()
            return df_main

        ts_col = self.main.timestamp_col
        if ts_col not in df_main.columns:
            raise RuntimeError(f"Dataset '{self.name}': columna '{ts_col}' no existe")

        if not pd.api.types.is_datetime64_any_dtype(df_main[ts_col]):
            df_main[ts_col] = pd.to_datetime(df_main[ts_col], unit="s", errors="coerce")

        df_main = df_main.sort_values(self.main.timestamp_col)

        # 2. EPOCH
        if self.epoch is None:
            return df_main

        out_path = self.epoch.epoch_processed_root / self.epoch.name / self.epoch.parquet_path.name
        
        # 🔥 MAGIA MULTIPROCESO
        if not out_path.exists() and allow_async:
            global global_epoch_process
            
            logging.info(f"🚀 Lanzando Epoch en proceso separado para '{self.name}'. UI liberada.")
            
            # Lanzamos el nuevo proceso
            global_epoch_process = multiprocessing.Process(target=self.epoch.load_or_process_epoch)
            global_epoch_process.daemon = True
            global_epoch_process.start()
            
            return df_main 

        logging.info(f"🧩 Dataset '{self.name}': cargando Epoch '{self.epoch.name}'")
        df_epoch = self.epoch.load_or_process_epoch()

        # 3. MERGE EN RAM
        df_merged = df_main.merge(
            df_epoch, how="left", left_on=self.main.timestamp_col,
            right_on=self.epoch.merge_on, suffixes=("", "_epoch")
        )
        return df_merged