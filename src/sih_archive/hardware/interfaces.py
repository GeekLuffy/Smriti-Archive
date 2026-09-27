"""
Abstract Interfaces for Hardware Workstations, Archival Servers, and Kiosk Displays.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from sih_archive.hardware.schemas import (
    ArchivalStorageNode,
    KioskDisplayProfile,
    SyncStatus,
    WorkstationCaptureConfig,
)
from sih_archive.schemas.ocr import OCROutput


class DigitizationWorkstation(ABC):
    """Abstract interface for archival digitization workstations."""

    @abstractmethod
    def configure_capture(self, config: WorkstationCaptureConfig) -> None:
        """Applies hardware capture parameters (resolution, lighting, color mode)."""
        pass

    @abstractmethod
    def acquire_page_image(self, target_output_path: Path) -> Path:
        """Captures a raw archival image from optical/sensor hardware."""
        pass


class ArchivalStorageServer(ABC):
    """Abstract interface for institutional archival storage and local cache."""

    @abstractmethod
    def register_node(self, node: ArchivalStorageNode) -> None:
        """Registers an on-premise storage partition."""
        pass

    @abstractmethod
    def check_synchronization(self) -> SyncStatus:
        """Checks synchronization state with central archival repository."""
        pass


class KioskDisplayController(ABC):
    """Abstract interface driving interactive visitor hardware displays."""

    @abstractmethod
    def load_display_profile(self, profile: KioskDisplayProfile) -> None:
        """Configures touch, audio, and language display settings."""
        pass

    @abstractmethod
    def render_page_with_bounding_boxes(
        self,
        image_path: Path,
        regions: List[dict],
    ) -> bool:
        """Directs display hardware to highlight specific OCR citation regions on screen."""
        pass
