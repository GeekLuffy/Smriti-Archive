"""
Data Schemas for Hardware Abstraction and Institutional Storage / Kiosk Interfaces.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class WorkstationCaptureConfig(BaseModel):
    """Configuration interface for digitization hardware capture."""
    target_dpi: int = Field(default=300, ge=150, le=1200)
    color_mode: str = Field(default="rgb24", pattern="^(rgb24|gray8|bitonal)$")
    scanner_model_str: Optional[str] = Field(None, description="Make/model of camera scanner or flatbed.")
    calibrated_lux: Optional[float] = Field(None, ge=0.0, description="Measured lighting illumination level.")


class ArchivalStorageNode(BaseModel):
    """Archival server node representation for on-premise institutional storage."""
    node_id: str = Field(..., description="Unique institutional storage node identifier.")
    mount_point: str = Field(..., description="Filesystem directory for immutable archival assets.")
    is_read_only: bool = Field(default=True, description="Strict write-protection for preservation.")
    redundancy_level: str = Field(default="local_mirror", description="Storage redundancy configuration.")


class KioskDisplayProfile(BaseModel):
    """Interactive visitor hardware display profile for museum or memorial deployment."""
    kiosk_id: str = Field(..., description="Physical kiosk station identifier.")
    resolution: List[int] = Field(..., min_length=2, max_length=2, description="Width and height in pixels.")
    touch_enabled: bool = Field(default=True)
    audio_enabled: bool = Field(default=True)
    active_language: str = Field(default="eng", pattern="^[a-z]{3}$")


class SyncStatus(BaseModel):
    """Synchronization telemetry between edge kiosk/workstation and institutional central archive."""
    last_sync_utc: Optional[str] = Field(None)
    pending_items_count: int = Field(default=0, ge=0)
    state: str = Field(default="idle", pattern="^(idle|syncing|offline|error)$")
    bytes_transferred: int = Field(default=0, ge=0)
