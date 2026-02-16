# config_env.py — configuración centralizada con Pydantic Settings
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import json
from typing import Optional

class Settings(BaseSettings):
    # --- SERVER CONFIG ---
    SERVER_PORT: int = 8050

    # --- MLOPS CONFIG ---
    EXECUTIONS_ROOT: str = "./MLOPS_Simulado/executions"
    EXPLORE_STAGE: str = "01_explore"
    EVENTS_STAGE: str = "02_prepareeventsds"
    OUTPUT_CONTROL: str = "MLOPS_Simulado/control.yml"
    # DEFAULT_DATASET: str = "MDS-Complete-v003"
    DEFAULT_DATASET: str = "MDS-Complete-v003"

    TIMESTAMP_COL: str = "segs"
    EPOCH_EVENT_COLS: list = ["event", "event_id", "evt", "code", "codigo_evento", "event_code","events"]
    CONTROL_DATASET_FILE: str = "control_dataset.yml"
    EPOCH_MODE: bool = True

    EPOCH_PROCESSED_DIR: str = "./epoch_processed"

    CTRL_COMPONENTS_TEMPORAL: str = "ctl_components_temporal.yml"

    CTRL_COMPONENTS_EPOCH: str = "ctl_components_epoch.yml"
    CTRL_COMPONENTS_EPOCH_DICTIONARY: str = "02_prepareeventsds_event_catalog.json"
    CTRL_COMPONENTS_EPOCH_METADATA: str = "02_prepareeventsds_metadata.json"


    # Configuración de carga
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # Ignora variables en el .env que no estén definidas aquí
    )

    @field_validator("EPOCH_EVENT_COLS", mode="before")
    @classmethod
    def _coerce_epoch_event_cols(cls, value):
        if isinstance(value, list):
            return value
        if value is None:
            return value
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    pass
            return [item.strip() for item in raw.split(",") if item.strip()]
        return value


# Instancia global
settings_env = Settings()