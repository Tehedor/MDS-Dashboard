import logging
import json
from pathlib import Path
import pandas as pd
import yaml


class DatasetComposite:
    def __init__(self, name, registry, subdatasets):
        self.name = name
        self.registry = registry
        self.subdatasets_cfg = subdatasets

        logging.info(f"🧩 Iniciando DatasetComposite '{name}'")

        # Carpeta donde guardamos los parquets compuestos
        self.composed_dir = registry.root / ".processed-composed"
        self.composed_dir.mkdir(exist_ok=True)
        self.composed_parquet = self.composed_dir / f"{name}.parquet"

        # ------------------------------------------------------------
        # 🚀 Si el parquet compuesto ya existe → cargarlo
        # ------------------------------------------------------------
        if self.composed_parquet.exists():
            logging.info(f"🧩 Cargando parquet compuesto: {self.composed_parquet}")

            self.df = pd.read_parquet(self.composed_parquet)

            # reconstruir main y secondary
            main_name = subdatasets["main"]
            self.main = registry.subdatasets[main_name]
            self.secondary = {
                k: registry.subdatasets[v]
                for k, v in subdatasets.items()
                if k != "main" and v
            }

            # reconstruir sets de eventos
            self.raw_codes, self.from_to_codes = self._load_grouped_dictionary()
            self.event_dict = self._build_event_dict()

            return

        # ------------------------------------------------------------
        # 🚀 Si no existe → construir composite entero
        # ------------------------------------------------------------
        logging.info(f"🧩 Construyendo composite desde cero: {name}")

        main_name = subdatasets["main"]
        self.main = registry.subdatasets[main_name]

        self.secondary = {
            k: registry.subdatasets[v]
            for k, v in subdatasets.items()
            if k != "main" and v
        }

        # separar tipos de eventos
        self.raw_codes, self.from_to_codes = self._load_grouped_dictionary()

        # construir df final
        self.df = self._build_combined_df()

        # dividir en state/from_to
        self._split_event_types()

        # construir diccionario de eventos
        self.event_dict = self._build_event_dict()

        # guardar parquet compuesto
        self.df.to_parquet(self.composed_parquet, index=False)
        logging.info(f"🧩 Parquet compuesto guardado: {self.composed_parquet}")

    # ---------------------------------------------------------------------
    def _load_grouped_dictionary(self):
        path = self.registry.root / "Epoch-Dataset" / "control_groupedDictionary.yml"
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        raw_codes = set()
        from_to_codes = set()

        for comp, data in cfg["components"].items():
            meas = data["measurements"]
            raw_codes.update(meas["raw"]["columns_encoded"])
            from_to_codes.update(meas["from_to"]["columns_encoded"])

        return raw_codes, from_to_codes

    # ---------------------------------------------------------------------
    def _build_combined_df(self):
        df = self.main.df.copy()

        for key, sd in self.secondary.items():
            logging.info(f"🧩 Integrando '{key}' (type={sd.type})")
            if sd.type == "event-encoded":
                df = self._merge_event_encoded(df, sd)
            else:
                df = df.merge(
                    sd.df,
                    on=sd.timestamp_col,
                    how="left",
                    suffixes=("", f"_{key}")
                )
            logging.info(f"🧩   → filas={len(df)}, cols={len(df.columns)}")

        return df

    # ---------------------------------------------------------------------
    def _merge_event_encoded(self, df_main, sd):
        ts_col = sd.timestamp_col

        df_evt = sd.df[[ts_col, "event_code"]].copy()
        df_evt = df_evt.sort_values(ts_col)
        df_main = df_main.sort_values(ts_col)

        logging.info("🧩 agrupando eventos…")
        grouped = (
            df_evt.groupby(ts_col)["event_code"]
                .agg(list)
                .rename("events")
                .reset_index()
        )

        out = df_main.merge(grouped, on=ts_col, how="left")

        # vectorizado seguro
        out["events"] = out["events"].apply(
            lambda x: x if isinstance(x, list) else []
        )

        return out

    # ---------------------------------------------------------------------
    def _split_event_types(self):
        """
        Crea:
        - events_state     → eventos RAW ordenados de menor a mayor
        - events_from_to   → eventos FROM_TO ordenados de menor a mayor
        """

        # 🛑 Si no hay eventos, salir
        if "events" not in self.df.columns:
            logging.info(f"🧩 Dataset '{self.name}' no contiene eventos → skip split_event_types()")
            return

        df = self.df

        # --- STATE EVENTS ---
        df["events_state"] = df["events"].apply(
            lambda lst: sorted(
                [e for e in lst if e in self.raw_codes]
            )
        )

        # --- FROM_TO EVENTS ---
        df["events_from_to"] = df["events"].apply(
            lambda lst: sorted(
                [e for e in lst if e in self.from_to_codes]
            )
        )

        # Ya no necesitamos la columna original
        df.drop(columns=["events"], inplace=True)

    # ---------------------------------------------------------------------
    def _build_event_dict(self):
        final = {}

        for sd in self.secondary.values():
            if sd.type != "event-encoded":
                continue

            dict_path = sd.path / "Events_Dictionary.json"
            with open(dict_path, "r") as f:
                raw = json.load(f)

            mapping = {code: name for name, code in raw.items()}

            for code, name in mapping.items():
                var = name.split("_Q")[0] if "_Q" in name else name

                if code in self.raw_codes:
                    etype = "state"
                elif code in self.from_to_codes:
                    etype = "from_to"
                else:
                    etype = "unknown"

                final[code] = {
                    "name": name,
                    "var": var,
                    "type": etype
                }

        return final

    # ---------------------------------------------------------------------
    def get_event_dict(self):
        return self.event_dict

    # ---------------------------------------------------------------------
    def info(self):
        return {
            "name": self.name,
            "rows": len(self.df),
            "cols": list(self.df.columns),
            "has_events": "events_state" in self.df.columns,
            "num_event_codes": len(self.event_dict),
        }
