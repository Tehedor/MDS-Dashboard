# utils/dataset/DatasetComposite.py
import logging
from duckdb import df
import pandas as pd


class DatasetComposite:


    def __init__(self, name, registry, subdatasets):
        self.name = name
        self.registry = registry
        self.subdatasets_cfg = subdatasets

        logging.info(f"🧩 Iniciando DatasetComposite '{name}'")

        # carpeta de salida para parquets compuestos
        self.composed_dir = registry.root / ".processed-composed"
        self.composed_dir.mkdir(exist_ok=True)
        self.composed_parquet = self.composed_dir / f"{name}.parquet"

        # ========================================================
        #   SI EL PARQUET YA EXISTE → cargar y reconstruir referencias
        # ========================================================
        if self.composed_parquet.exists():
            logging.info(f"🧩 Cargando parquet compuesto existente: {self.composed_parquet}")

            # cargar parquet (esperamos que contenga la columna 'Timestamp')
            self.df = pd.read_parquet(self.composed_parquet)

            # asegurarnos de que Timestamp existe y el índice es DatetimeIndex
            if "Timestamp" in self.df.columns:
                self.df["Timestamp"] = pd.to_datetime(self.df["Timestamp"], errors="coerce")
                # establecer índice a partir de la columna Timestamp (sin eliminarla)
                self.df.index = self.df["Timestamp"]
            else:
                # si no hay columna Timestamp, intentar usar el índice ya presente
                if not isinstance(self.df.index, pd.DatetimeIndex):
                    # forzar conversión del índice a datetime
                    try:
                        self.df.index = pd.to_datetime(self.df.index, errors="coerce")
                    except Exception:
                        pass

            # reconstruir referencias a subdatasets
            main_name = subdatasets["main"]
            self.main = registry.subdatasets[main_name]

            self.secondary = {}
            for key, sd_name in subdatasets.items():
                if key == "main":
                    continue

                if sd_name is None:
                    logging.info(f"ℹ️ Subdataset '{key}' = None → ignorado en composite '{self.name}'")
                    continue

                if sd_name not in registry.subdatasets:
                    logging.warning(f"⚠️ Subdataset '{sd_name}' no existe en registry. Ignorado.")
                    continue

                self.secondary[key] = registry.subdatasets[sd_name]

            return

        # ========================================================
        #   CONSTRUCCIÓN DESDE CERO
        # ========================================================
        logging.info(f"🧩 Construyendo composite desde cero: {name}")

        # main dataset
        main_name = subdatasets["main"]
        self.main = registry.subdatasets[main_name]

        # otros subdatasets
        self.secondary = {}
        for key, sd_name in subdatasets.items():
            if key == "main":
                continue

            if sd_name is None:
                logging.info(f"ℹ️ Subdataset '{key}' = None → no se mergea")
                continue

            if sd_name not in registry.subdatasets:
                logging.warning(f"⚠️ Subdataset '{sd_name}' declarado pero NO existe. Ignorado.")
                continue

            self.secondary[key] = registry.subdatasets[sd_name]

        # merge final (devuelve df con índice datetime)
        self.df = self._build_combined_df()

        # --- aquí sacamos el índice a columna Timestamp (columna real) ---
        # asegurar que el índice es DatetimeIndex
        if not isinstance(self.df.index, pd.DatetimeIndex):
            try:
                self.df.index = pd.to_datetime(self.df.index, errors="coerce")
            except Exception:
                pass

        # crear columna Timestamp basada en el índice (mantener índice también)
        self.df["Timestamp"] = self.df.index

        # guardar parquet final SIN índice (Timestamp queda como columna)
        self.df.to_parquet(self.composed_parquet, index=False)
        logging.info(f"🧩 Parquet compuesto guardado: {self.composed_parquet}")

    # =====================================================================
    #   MERGE DIRECTO POR ÍNDICE
    # =====================================================================
    def _build_combined_df(self):
        """
        Combina:
        - main dataset
        - secundarios (tabular o event-encoded)
        
        Merge LEFT basado en índice (Timestamp).
        """

        df = self.main.df.copy()

        for key, sd in self.secondary.items():
            logging.info(f"🧩 Mergeando '{key}' (type={sd.type})")

            df = df.merge(
                sd.df,
                left_index=True,
                right_index=True,
                how="left",
                suffixes=("", f"_{key}")
            )

            logging.info(f"   → filas={len(df)}, columnas={len(df.columns)}")

        return df

    # =====================================================================
    #   INFO DEL DATASET
    # =====================================================================
    def info(self):
        return {
            "name": self.name,
            "rows": len(self.df),
            "cols": list(self.df.columns),
            "num_columns": len(self.df.columns)
        }

    # =====================================================================
    #   GET ALL COLUMNS (FRONT-END)
    # =====================================================================
    def get_all_columns(self):
        """
        Devuelve TODA la metadata necesaria para el frontend:
        - columnas tabulares (reales en el parquet)
        - columnas de eventos (raw / from_to) desde ctl_components.yml
        - agrupación por componentes
        - etiquetas amigables
        """

        df_cols = list(self.df.columns)

        # ============================================================
        # 1) TABULARES
        # ============================================================
        tabular_cols = []
        main_comp_meta = self.main.componentes.get("components", {})

        for comp_id, comp_data in main_comp_meta.items():
            for meas_key, meas_info in comp_data.get("measurements", {}).items():

                display = meas_info.get("display_name", meas_key)

                if display in df_cols:
                    tabular_cols.append({
                        "name": display,
                        "type": "tabular",
                        "component": comp_id
                    })

        # ============================================================
        # 2) EVENTOS (ctl_components.yml de event-encoded)
        # ============================================================
        event_raw = []
        event_from_to = []
        by_component = {}

        # localizar el único event-encoded
        event_sd = None
        for sd in self.secondary.values():
            if sd.type.lower() == "eventencodeddataset":
                event_sd = sd
                break

        if event_sd is None:
            # no hay eventos → solo tabulares
            return {
                "tabular": tabular_cols,
                "event_raw": [],
                "event_from_to": [],
                "all": tabular_cols,
                "by_component": {},
                "components_meta": main_comp_meta,
                "component_display_map": {
                    cid: cdata.get("name", cid)
                    for cid, cdata in main_comp_meta.items()
                }
            }

        yaml_components = event_sd.componentes.get("components", {})

        # recorrer componentes
        for comp_id, comp_data in yaml_components.items():

            for meas_key, meas_info in comp_data.get("measurements", {}).items():

                display = meas_info.get("display_name", meas_key)
                encodes = meas_info.get("encodes", [])
                labels = meas_info.get("labels", [])
                mtype = meas_info.get("type")

                base_item = {
                    "name": display,
                    "component": comp_id,
                    "codes": encodes,
                    "labels": labels,
                }

                if mtype == "event":
                    item = {**base_item, "type": "raw"}
                    event_raw.append(item)

                elif mtype == "from_to":
                    item = {**base_item, "type": "from_to"}
                    event_from_to.append(item)

                by_component.setdefault(comp_id, []).append(base_item)

        # ============================================================
        # 3) UNIFICAR META
        # ============================================================
        components_meta = dict(main_comp_meta)

        # añadir los componentes de eventos si no existen
        for comp_id, comp_data in yaml_components.items():
            if comp_id not in components_meta:
                components_meta[comp_id] = comp_data

        component_display_map = {
            cid: cdata.get("name", cid)
            for cid, cdata in components_meta.items()
        }

        # ============================================================
        # 4) SALIDA FINAL
        # ============================================================
        return {
            "tabular": tabular_cols,
            "event_raw": event_raw,
            "event_from_to": event_from_to,
            "all": tabular_cols + event_raw + event_from_to,
            "by_component": by_component,
            "components_meta": components_meta,
            "component_display_map": component_display_map,
        }
