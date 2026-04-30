# config_env.py — configuración centralizada con Pydantic Settings
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import json

class Settings(BaseSettings):
    # --- SERVER CONFIG ---
    SERVER_PORT: int = 8050
    ASYNC_EPOCH_PROCESSING: bool = True

    # --- MLOPS CONFIG ---
    EXECUTIONS_ROOT: str = "./executions"
    EXPLORE_STAGE: str = "f01_explore"
    EVENTS_STAGE: str = "f02_events"
    OUTPUT_CONTROL: str = "control.yml"
    # DEFAULT_DATASET: str = "MDS-Complete-v003"
    DEFAULT_DATASET: str = "MDS-Complete-v1_0003"

    TIMESTAMP_COL: str = "segs"
    EPOCH_EVENT_COLS: list = ["event", "event_id", "evt", "code", "codigo_evento", "event_code","events"]
    CONTROL_DATASET_FILE: str = "control_dataset.yml"
    EPOCH_MODE: bool = True

    EPOCH_PROCESSED_DIR: str = "./epoch_processed"

    CTRL_COMPONENTS_TEMPORAL: str = "ctl_components_temporal.yml"

    CTRL_COMPONENTS_EPOCH: str = "ctl_components_epoch.yml"
    CTRL_COMPONENTS_EPOCH_DICTIONARY: str = "02_events_catalog.json"
    # CTRL_COMPONENTS_EPOCH_METADATA: str = "02_prepareeventsds_metadata.json"
    CTRL_COMPONENTS_EPOCH_METADATA: str = "params.yaml"
    CTRL_COMPONENTS_EPOCH_METADATA_CANDIDATES: list = [
        "params.yaml",
        "metadata.yaml",
        "outputs.yaml",
        "02_prepareeventsds_metadata.json",
    ]


    # Configuración de carga
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # Ignora variables en el .env que no estén definidas aquí
    )

    @field_validator("EPOCH_EVENT_COLS", mode="before")
    @classmethod
    def _coerce_epoch_event_cols(cls, value):
        return cls._coerce_string_list(value)

    @field_validator("CTRL_COMPONENTS_EPOCH_METADATA_CANDIDATES", mode="before")
    @classmethod
    def _coerce_epoch_metadata_candidates(cls, value):
        return cls._coerce_string_list(value)

    @staticmethod
    def _coerce_string_list(value):
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