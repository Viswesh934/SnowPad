"""SnowPad configuration and path settings."""

from pathlib import Path
from pydantic import BaseModel, Field

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DB_PATH = DATA_DIR / "snowpad.duckdb"

class Settings(BaseModel):
    """Runtime configuration for SnowPad."""
    app_name: str = "SnowPad"
    version: str = "0.1.0"
    db_path: Path = Field(default=DEFAULT_DB_PATH)
    
    # Circle of Scope defaults
    default_scope_radius: float = Field(default=1.0, description="Threshold radius for Circle of Scope")
    
    # Active reporting quarter
    active_quarter: str = "Q4-2026"

settings = Settings()
