# utils/dataset/procesor.py
from pathlib import Path
import pandas as pd
import json
from typing import Optional
from utils.dataset.loader import read_csvs_concat, save_parquet, load_parquet

# NOTE: aquí puedes integrar tus clean_functions si quieres ejecutar la pipeline completa.
# Para mantenerlo robusto y simple, implementamos una limpieza mínima por defecto.

def build_mds_parquet(raw_dir: Path, out_parquet: Path, timestamp_col: str = "Timestamp"):
    csvs = sorted(raw_dir.glob("*.csv"))
    if not csvs:
        raise FileNotFoundError(f"No CSVs found in {raw_dir}")
    df = read_csvs_concat(csvs, parse_dates=[timestamp_col])
    # ordena y normaliza timestamp minimalmente
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    df = df.sort_values(timestamp_col).reset_index(drop=True)
    save_parquet(df, out_parquet)
    return out_parquet

def build_epoch_parquet(raw_csv: Path, event_dict_path: Path, out_parquet: Path, ts_unit: str = "s"):
    if not raw_csv.exists():
        raise FileNotFoundError(f"Epoch raw file not found: {raw_csv}")
    df = pd.read_csv(raw_csv)
    # asumimos la columna 'Timestamp' en epoch seconds o nombre 'Timestamp'
    if df["Timestamp"].dtype == "int64" or df["Timestamp"].dtype == "float64":
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit=ts_unit)
    else:
        try:
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        except Exception:
            # fallback: treat as epoch
            df["Timestamp"] = pd.to_datetime(df["Timestamp"].astype(int), unit=ts_unit)

    # cargar mapping event_code -> event_name
    with open(event_dict_path, "r", encoding="utf-8") as fh:
        mapping = json.load(fh)
    inv = {v: k for k, v in mapping.items()}

    df["event_name"] = df["event"].map(inv)
    # derive var (component) and keep event code
    # - event_name examples: "Battery_Active_Power_from_Q05_to_Q10"
    df["var"] = df["event_name"].str.split("_from_").str[0].fillna(method="ffill")
    # si var contiene suffix like _Q05, remueve
    df["var"] = df["var"].str.replace(r"_Q\d+$", "", regex=True)

    # salvar parquet
    save_parquet(df, out_parquet)
    return out_parquet

def load_or_build_mds_parquet(raw_dir: Path, out_parquet: Path):
    if out_parquet.exists():
        return out_parquet
    return build_mds_parquet(raw_dir, out_parquet)

def load_or_build_epoch_parquet(raw_csv: Path, event_dict_path: Path, out_parquet: Path):
    if out_parquet.exists():
        return out_parquet
    return build_epoch_parquet(raw_csv, event_dict_path, out_parquet)
