# utils/dataset/DatasetComposite.py
import logging
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
        #   SI EL PARQUET YA EXISTE → cargar y salir
        # ========================================================
        if self.composed_parquet.exists():
            logging.info(f"🧩 Cargando parquet compuesto existente: {self.composed_parquet}")

            self.df = pd.read_parquet(self.composed_parquet)

            # reconstruir referencias
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
        #   SI NO EXISTE → construir composite desde cero
        # ========================================================
        logging.info(f"🧩 Construyendo composite desde cero: {name}")

        # main dataset
        main_name = subdatasets["main"]
        self.main = registry.subdatasets[main_name]

        # otros subdatasets (con soporte para null)
        self.secondary = {}
        for key, sd_name in subdatasets.items():
            if key == "main":
                continue

            if sd_name is None:
                logging.info(f"ℹ️ Subdataset '{key}' = None → no se mergea en composite '{self.name}'")
                continue

            if sd_name not in registry.subdatasets:
                logging.warning(f"⚠️ Subdataset '{sd_name}' declarado pero NO existe. Ignorado.")
                continue

            self.secondary[key] = registry.subdatasets[sd_name]

        # construir dataframe final
        self.df = self._build_combined_df()

        # guardar parquet final
        self.df.to_parquet(self.composed_parquet, index=False)
        logging.info(f"🧩 Parquet compuesto guardado: {self.composed_parquet}")

    # =====================================================================
    #   MERGE DIRECTO SIN PROCESAR COLUMNAS
    # =====================================================================
    def _build_combined_df(self):
        """
        Combina:
        - el subdataset principal (tabular)
        - los subdatasets secundarios
        Hace simple LEFT MERGE por timestamp.

        NO crea columnas nuevas.
        NO procesa nada.
        """

        df = self.main.df.copy()

        for key, sd in self.secondary.items():
            logging.info(f"🧩 Mergeando '{key}' (type={sd.type})")

            df = df.merge(
                sd.df,
                on=sd.timestamp_col,
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
    #   GET ALL COLUMNS → tabular + events (basado solo en columnas reales)
    # =====================================================================
    def get_all_columns(self):
        """
        Devuelve TODA la metadata necesaria para la UI:
        - columnas tabulares
        - columnas de eventos (raw / from_to)
        - agrupación por componentes
        - mapa de nombres amigables
        """

        df_cols = list(self.df.columns)

        # ============================================================
        # 1) TABULARES (del main dataset)
        # ============================================================
        tabular_cols = []
        tabular_measure_map = {}

        main_comp_meta = {}
        if hasattr(self.main, "componentes"):
            main_comp_meta = self.main.componentes.get("components", {})

        for comp_id, comp_data in main_comp_meta.items():
            meas = comp_data.get("measurements", {})
            for meas_key, meas_info in meas.items():

                display = meas_info.get("display_name", meas_key)

                if display in df_cols:
                    tabular_cols.append({
                        "name": display,
                        "type": "tabular",
                        "component": comp_id
                    })
                    tabular_measure_map[display] = comp_id

        # ============================================================
        # 2) EVENTOS (YA NO SE TOMAN DE COLUMNAS → SE OBTIENEN DEL YAML)
        # ============================================================

        event_raw = []
        event_from_to = []
        by_component = {}

        # 2.1 detectar el subdataset event-encoded que existe en el composite
        event_sd = None
        for sd in self.secondary.values():
            if sd.type == "event-encoded":
                event_sd = sd
                break

        if event_sd is None:
            # no hay eventos en este dataset
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

        # ============================
        # 2.2 RECORRER YAML AGRUPADO
        # ============================
        for comp_id, comp_data in yaml_components.items():

            measurements = comp_data.get("measurements", {})
            for meas_key, meas_info in measurements.items():

                meas_name = meas_info.get("name", meas_key)
                meas_blocks = meas_info.get("measurements", {})

                for block_key, block_data in meas_blocks.items():

                    encoded = block_data.get("columns_encoded", [])
                    if not encoded:
                        continue

                    base_item = {
                        "component": comp_id,
                        "measurement": meas_name,
                        "codes": encoded,
                    }

                    if block_key.endswith("-raw"):
                        item = {
                            **base_item,
                            "name": f"{meas_name}_raw",
                            "type": "raw",
                        }
                        event_raw.append(item)
                        by_component.setdefault(comp_id, []).append(item)

                    elif block_key.endswith("-from_to"):
                        item = {
                            **base_item,
                            "name": f"{meas_name}_from_to",
                            "type": "from_to",
                        }
                        event_from_to.append(item)
                        by_component.setdefault(comp_id, []).append(item)

        # ============================================================
        # 3) COMPONENTES META (mezcla tabular + eventos)
        # ============================================================
        components_meta = {}

        # primero tabular
        for comp_id, comp_data in main_comp_meta.items():
            components_meta[comp_id] = comp_data

        # añadir los de eventos si no existen en tabular
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
