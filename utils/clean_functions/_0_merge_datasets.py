import logging
from math import log
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
        file_pattern: patrón glob (ej. "-dataset/*.csv") o lista de patrones/rutas.
        max_files: si se indica, limita la cargMDSa a los primeros N archivos.
        year_filter: si se indica, filtra los archivos cuyo nombre contiene este texto.

    Returns:
        pd.DataFrame: DataFrame combinado con índice datetime en la columna 'Timestamp'.
    """
    # Normalizar a lista de patrones
    patterns = list(file_pattern) if isinstance(file_pattern, (list, tuple)) else [file_pattern]
    logging.info(f"🔍 Buscando archivos con patrones: {patterns}")
    # Resolver patrones a rutas de fichero reales
    file_list: List[str] = []
    for p in patterns:
        # si es una ruta existente la usamos tal cual, si no tratamos como glob
        if isinstance(p, str) and os.path.isfile(p):
            file_list.append(p)
        else:
            file_list.extend(glob.glob(p))

    logging.info(f"✅ {len(file_list)} archivos encontrados antes de filtros")
    # Filtrar por year_filter si aplica
    if year_filter:
        file_list = [f for f in file_list if year_filter in os.path.basename(f)]
        logging.info(f"📅 Filtrando archivos que contienen '{year_filter}' → {len(file_list)} encontrados")
    if not file_list:
        raise FileNotFoundError(f"No se encontraron archivos con patrón(s) {patterns} y filtro {year_filter}")

    if max_files is not None:
        file_list = file_list[:max_files]
        logging.info(f"⚙️ Limitando a los primeros {max_files} archivos")

    logging.info(f"{len(file_list)} archivos encontrados:")
    for file_path in file_list:
        logging.info(f"  -> {os.path.basename(file_path)}")
    logging.info("-" * 50)


    data_frames: List[pd.DataFrame] = []
    for file in file_list:
        # Lectura defensiva: usar separador coma y decimal punto tal y como pediste
        df_piece = pd.read_csv(file, sep=',', decimal='.')
        data_frames.append(df_piece)
        logging.info(f"   ✔️ Cargado {os.path.basename(file)} con {len(df_piece)} filas y {len(df_piece.columns)} columnas")

    df = pd.concat(data_frames, ignore_index=True)
    logging.info(f"📊 DataFrame combinado tiene {len(df)} filas y {len(df.columns)} columnas")
    # Procesar timestamps
    logging.info(f"Número de filas antes de procesar timestamps: {len(df)}")
    if 'Timestamp' not in df.columns:
        raise KeyError("Columna 'Timestamp' no encontrada en los archivos cargados")

    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df.dropna(subset=['Timestamp'], inplace=True)
    logging.info(f"Número de filas después de eliminar timestamps inválidos: {len(df)}")

    df.set_index('Timestamp', inplace=True)
    df.sort_index(inplace=True)

    return df
