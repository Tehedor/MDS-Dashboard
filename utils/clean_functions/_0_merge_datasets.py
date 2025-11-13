import os
import glob
from typing import List, Optional, Union

import pandas as pd


def merge_all_datasets(
    file_pattern: Union[str, List[str]],
    max_files: Optional[int] = None,
    year_filter: Optional[str] = None,
) -> pd.DataFrame:
    """
    Carga y concatena múltiples CSV en un único DataFrame listo para que el resto
    de la pipeline opere sobre un solo dataset.

    Args:
        file_pattern: patrón glob (ej. "MDS-dataset/*.csv") o lista de patrones/rutas.
        max_files: si se indica, limita la carga a los primeros N archivos.
        year_filter: si se indica, filtra los archivos cuyo nombre contiene este texto.

    Returns:
        pd.DataFrame: DataFrame combinado con índice datetime en la columna 'Timestamp'.
    """
    # Normalizar a lista de patrones
    patterns = list(file_pattern) if isinstance(file_pattern, (list, tuple)) else [file_pattern]

    # Resolver patrones a rutas de fichero reales
    file_list: List[str] = []
    for p in patterns:
        # si es una ruta existente la usamos tal cual, si no tratamos como glob
        if isinstance(p, str) and os.path.isfile(p):
            file_list.append(p)
        else:
            file_list.extend(glob.glob(p))

    # Filtrar por year_filter si aplica
    if year_filter:
        file_list = [f for f in file_list if year_filter in os.path.basename(f)]
        print(f"📅 Filtrando archivos que contienen '{year_filter}' → {len(file_list)} encontrados")

    if not file_list:
        raise FileNotFoundError(f"No se encontraron archivos con patrón(s) {patterns} y filtro {year_filter}")

    if max_files is not None:
        file_list = file_list[:max_files]
        print(f"⚙️ Limitando a los primeros {max_files} archivos")

    print(f"{len(file_list)} archivos encontrados:")
    for file_path in file_list:
        print(f"  -> {os.path.basename(file_path)}")
    print("-" * 50)

    data_frames: List[pd.DataFrame] = []
    for file in file_list:
        # Lectura defensiva: usar separador coma y decimal punto tal y como pediste
        df_piece = pd.read_csv(file, sep=',', decimal='.')
        data_frames.append(df_piece)

    df = pd.concat(data_frames, ignore_index=True)

    # Procesar timestamps
    print("Número de filas antes de procesar timestamps:", len(df))
    if 'Timestamp' not in df.columns:
        raise KeyError("Columna 'Timestamp' no encontrada en los archivos cargados")

    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df.dropna(subset=['Timestamp'], inplace=True)
    print("Número de filas después de eliminar timestamps inválidos:", len(df))

    df.set_index('Timestamp', inplace=True)
    df.sort_index(inplace=True)

    return df
