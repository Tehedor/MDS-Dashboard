# utils/dataset/DatasetComposite.py
import logging
import pandas as pd

from config_env import settings_env

class DatasetComposite:
    """
    DatasetComposite
    =================
    Representa un Dataset lógico seleccionable en la app.

    Responsabilidades:
      - Resolver SubDatasets
      - Cargar tabular (main)
      - Procesar y cargar Epoch si existe
      - Mergear en RAM
      - Devolver df listo para visualización

    ❌ NO escribe a disco
    ❌ NO cachea
    """

    def __init__(self, name, registry, subdatasets):
        self.name = name
        self.registry = registry
        self.subdatasets_cfg = subdatasets

        # ------------------------------
        # Resolver subdatasets
        # ------------------------------
        main_name = subdatasets.get("main")
        if main_name is None:
            raise RuntimeError(
                f"Dataset '{name}' no define subdataset 'main'"
            )

        self.main = registry.subdatasets.get(main_name)
        if self.main is None:
            raise RuntimeError(
                f"Dataset '{name}': subdataset main '{main_name}' no existe"
            )

        self.epoch = None
        epoch_name = subdatasets.get("epoch")
        if epoch_name:
            self.epoch = registry.subdatasets.get(epoch_name)
            if self.epoch is None:
                raise RuntimeError(
                    f"Dataset '{name}': subdataset epoch '{epoch_name}' no existe"
                )

        logging.info(
            f"🧩 DatasetComposite '{self.name}' "
            f"(main={main_name}, epoch={epoch_name})"
        )

    # --------------------------------------------------
    # API PRINCIPAL
    # --------------------------------------------------
    def load_for_visualization(self) -> pd.DataFrame:
        """
        Carga y devuelve el DataFrame listo para visualización.

        Flujo:
          1. Cargar tabular (main)
          2. Si hay epoch:
               - cargar o procesar epoch
               - merge LEFT en RAM usando segs
          3. Devolver df final
        """

        # ------------------------------
        # 1. TABULAR
        # ------------------------------
        # df_main = self.main.load_df()

        # if self.epoch is None:
        #     return df_main
        


        # 1. TABULAR
        df_main = self.main.load_df()

        if not settings_env.EPOCH_MODE:
            # 2. EPOCH → procesar y guardar (sin merge)
            if self.epoch is not None:
                logging.info(
                    f"🧩 Dataset '{self.name}': procesando Epoch '{self.epoch.name}' (sin merge)"
                )
                self.epoch.load_or_process_epoch()

            # 3. DEVOLVER SOLO TABULAR
            return df_main


        # # ❌ NO mergear epoch aquí todavía
        # logging.info(
        #     f"🧩 Dataset '{self.name}': Epoch disponible pero no mergeado"
        # )
        # return df_main



        ts_col = self.main.timestamp_col
        if ts_col not in df_main.columns:
            raise RuntimeError(
                f"Dataset '{self.name}': columna temporal '{ts_col}' no existe"
            )

        # --------------------------------------------------
        # 🔥 NORMALIZACIÓN CLAVE DEL EJE TEMPORAL
        # --------------------------------------------------
        if not pd.api.types.is_datetime64_any_dtype(df_main[ts_col]):
            log_msg = f"⏱ Convirtiendo eje temporal '{ts_col}' desde epoch segundos"
            logging.info(log_msg)

            df_main[ts_col] = pd.to_datetime(
                df_main[ts_col],
                unit="s",
                errors="coerce"
            )

        # ordenar por tiempo
        df_main = df_main.sort_values(ts_col)

        # Asegurar orden temporal
        df_main = df_main.sort_values(self.main.timestamp_col)

        # ------------------------------
        # 2. EPOCH (opcional)
        # ------------------------------
        if self.epoch is None:
            logging.info(
                f"🧩 Dataset '{self.name}': sin Epoch → usando solo tabular"
            )
            return df_main

        logging.info(
            f"🧩 Dataset '{self.name}': cargando Epoch '{self.epoch.name}'"
        )

        df_epoch = self.epoch.load_or_process_epoch()

        if self.epoch.merge_on not in df_epoch.columns:
            raise RuntimeError(
                f"Dataset '{self.name}': "
                f"Epoch no contiene columna '{self.epoch.merge_on}'"
            )

        # ------------------------------
        # 3. MERGE EN RAM
        # ------------------------------
        df_merged = df_main.merge(
            df_epoch,
            how="left",
            left_on=self.main.timestamp_col,
            right_on=self.epoch.merge_on,
            suffixes=("", "_epoch")
        )

        logging.info(
            f"🧩 Dataset '{self.name}': "
            f"merge completado → filas={len(df_merged)}"
        )

        return df_merged


