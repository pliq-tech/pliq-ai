from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """AI service configuration loaded from environment variables."""

    grpc_host: str = Field(default="0.0.0.0", alias="GRPC_HOST")
    grpc_port: int = Field(default=50051, alias="GRPC_PORT")
    max_workers: int = Field(default=10, alias="MAX_WORKERS")

    google_api_key: str = Field(alias="GOOGLE_API_KEY")
    google_project_id: str = Field(default="", alias="GOOGLE_CLOUD_PROJECT")
    google_location: str = Field(default="us-central1", alias="GOOGLE_LOCATION")

    gemini_pro_model: str = Field(
        default="gemini-2.5-pro-preview-05-06", alias="GEMINI_PRO_MODEL"
    )
    gemini_flash_model: str = Field(
        default="gemini-2.5-flash-preview-05-20", alias="GEMINI_FLASH_MODEL"
    )
    embedding_model: str = Field(
        default="text-embedding-005", alias="EMBEDDING_MODEL"
    )

    fraud_ela_weight: float = Field(default=0.35, alias="FRAUD_ELA_WEIGHT")
    fraud_fft_weight: float = Field(default=0.25, alias="FRAUD_FFT_WEIGHT")
    fraud_exif_weight: float = Field(default=0.20, alias="FRAUD_EXIF_WEIGHT")
    fraud_reverse_weight: float = Field(default=0.20, alias="FRAUD_REVERSE_WEIGHT")
    fraud_detection_threshold: float = Field(
        default=0.7, alias="FRAUD_DETECTION_THRESHOLD"
    )

    log_level: str = Field(default="info", alias="LOG_LEVEL")

    model_config = {"env_prefix": "", "case_sensitive": True}

    @classmethod
    def from_env(cls) -> "Config":
        return cls()
