from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "JewelryAI Backend"
    app_env: str = "dev"
    log_level: str = "INFO"
    latency_target_max_ms: float = 1000.0
    latency_benchmark_iterations: int = 20
    sketch_analysis_backend: str = "deterministic"
    sketch_analysis_fallback_backend: str = "deterministic"
    sketch_analysis_allow_fallback: bool = True
    sketch_analysis_device: str = "cpu"
    sketch_analysis_grounded_sam_mode: str = "scaffold"
    grounding_dino_checkpoint_path: str | None = None
    sam2_checkpoint_path: str | None = None
    grounding_dino_model_id: str = "IDEA-Research/grounding-dino-base"
    sam2_model_id: str = "facebook/sam2-hiera-large"
    grounding_dino_box_threshold: float = 0.25
    grounding_dino_text_threshold: float = 0.25
    grounding_dino_local_files_only: bool = True
    component_placement_debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
