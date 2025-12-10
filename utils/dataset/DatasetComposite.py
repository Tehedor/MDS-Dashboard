# utils/dataset/DatasetComposite.py
import logging
import pandas as pd

from debug.debug import save_debug_info


class DatasetComposite:

    def __init__(self, name, registry, subdatasets):
        self.name = name
        self.registry = registry
        self.subdatasets_cfg = subdatasets

        logging.info(f"🧩 Iniciando DatasetComposite '{name}'")

        # carpeta de salida
        self.composed_dir = registry.root / ".processed-composed"
        self.composed_dir.mkdir(exist_ok=True)
        self.composed_parquet = self.composed_dir / f"{name}.parquet"

        # reconstrucción de referencias
        main_name = subdatasets["main"]
        self.main = registry.subdatasets[main_name]

        self.secondary = {}
        for key, sd_name in subdatasets.items():
            if key == "main" or sd_name is None:
                continue
            if sd_name in registry.subdatasets:
                self.secondary[key] = registry.subdatasets[sd_name]

        # ---------------------------------------------------------
        # Si ya existe parquet compuesto → NO cargamos df
        # ---------------------------------------------------------
        if self.composed_parquet.exists():
            logging.info(f"🧩 Parquet compuesto ya existe: {self.composed_parquet}")
            return

        # ---------------------------------------------------------
        # Construcción desde cero (solo generamos parquet)
        # ---------------------------------------------------------
        logging.info(f"🧩 Construyendo composite '{name}' desde cero…")

        df = self._build_combined_df()

        save_debug_info(
            content_source=df.head(10),
            filename=f"composite_{name}_head",
            head=f"HEADER DE DF compuesto '{name}' (primeras 100 filas)"
        )

        # Asegurar columna Timestamp
        if not isinstance(df.index, pd.DatetimeIndex):
            try:
                df.index = pd.to_datetime(df.index)
            except:
                pass

        df["Timestamp"] = df.index

        # Guardar parquet sin índice
        df.to_parquet(self.composed_parquet, index=False)

        # No conservar df en memoria
        del df

        logging.info(f"🧩 Parquet compuesto guardado: {self.composed_parquet}")

    # ==================================================================
    # MERGE DE SUBDATASETS
    # ==================================================================
    def _build_combined_df(self):
        df = self.main.load_df()

        for key, sd in self.secondary.items():
            logging.info(f"🧩 Mergeando '{key}' (type={sd.type})")

            sdf = sd.load_df()

            df = df.merge(
                sdf,
                left_index=True,
                right_index=True,
                how="left",
                suffixes=("", f"_{key}")
            )

        return df

    # ==================================================================
    # LAZY LOADING DEL PARQUET COMPUESTO
    # ==================================================================
    def _load_df_lazy(self):
        """Carga el df del parquet solo cuando la app lo necesita."""
        df = pd.read_parquet(self.composed_parquet)

        if "Timestamp" in df.columns:
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
            df.index = df["Timestamp"]

        return df

    # ==================================================================
    # INFO
    # ==================================================================
    def info(self):
        df = self._load_df_lazy()
        return {
            "name": self.name,
            "rows": len(df),
            "cols": list(df.columns),
            "num_columns": len(df.columns),
        }

    # ==================================================================
    # METADATOS PARA DASH
    # ==================================================================
    def get_all_columns(self):
        """
        Usa self.main.componentes + `ctl_components.yml` de eventos.
        No necesita df cargado en memoria.
        """

        # cargar df solo para ver columnas
        df = self._load_df_lazy()
        df_cols = list(df.columns)

        # componentes tabulares
        tabular_cols = []
        main_meta = self.main.componentes["components"]

        for cid, cdata in main_meta.items():
            for meas_key, meas_info in cdata["measurements"].items():
                display = meas_info.get("display_name", meas_key)
                if display in df_cols:
                    tabular_cols.append({
                        "name": display, "type": "tabular", "component": cid
                    })

        # localizar dataset de eventos
        event_sd = None
        for sd in self.secondary.values():
            if sd.type.lower() == "eventencodeddataset":
                event_sd = sd
                break

        if event_sd is None:
            return {
                "tabular": tabular_cols,
                "event_raw": [],
                "event_from_to": [],
                "all": tabular_cols,
                "by_component": {},
                "components_meta": main_meta,
                "component_display_map": {cid: cdata["name"] for cid, cdata in main_meta.items()},
            }

        yaml_components = event_sd.componentes["components"]

        event_raw = []
        event_from_to = []
        by_component = {}

        for cid, comp_data in yaml_components.items():

            for meas_key, meas_info in comp_data["measurements"].items():
                display = meas_info["display_name"]
                mtype = meas_info["type"]
                encodes = meas_info["encodes"]
                labels = meas_info["labels"]

                base_item = {
                    "name": display,
                    "component": cid,
                    "labels": labels,
                    "codes": encodes,
                }

                if mtype == "event":
                    event_raw.append({**base_item, "type": "raw"})
                elif mtype == "from_to":
                    event_from_to.append({**base_item, "type": "from_to"})

                by_component.setdefault(cid, []).append(base_item)

        components_meta = dict(main_meta)
        for cid in yaml_components:
            components_meta.setdefault(cid, yaml_components[cid])

        component_display_map = {
            cid: cdata.get("name", cid) for cid, cdata in components_meta.items()
        }

        return {
            "tabular": tabular_cols,
            "event_raw": event_raw,
            "event_from_to": event_from_to,
            "all": tabular_cols + event_raw + event_from_to,
            "by_component": by_component,
            "components_meta": components_meta,
            "component_display_map": component_display_map,
        }
