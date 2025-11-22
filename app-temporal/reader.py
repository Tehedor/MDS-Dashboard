# reader.py
import pandas as pd
from pathlib import Path

def load_csv(path: str):
    df = pd.read_csv(path)
    
    # Convertir columna timestamp si detectada
    first_col = df.columns[0]
    try:
        df[first_col] = pd.to_datetime(df[first_col])
    except:
        pass

    return df

def auto_load_dataset():
    """Busca un CSV en ./Datasets y lo carga automáticamente."""
    data_dir = Path("./Datasets")
    if not data_dir.exists():
        return None, None

    csvs = list(data_dir.glob("*.csv"))
    if not csvs:
        return None, None

    file = csvs[0]   # primer CSV
    df = load_csv(file)
    return df, file.name

