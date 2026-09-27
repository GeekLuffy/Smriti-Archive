"""Phase E5 Hardware and Institutional Deployment Interfaces."""

from sih_archive.hardware.interfaces import (
    ArchivalStorageServer,
    DigitizationWorkstation,
    KioskDisplayController,
)
from sih_archive.hardware.schemas import (
    ArchivalStorageNode,
    KioskDisplayProfile,
    SyncStatus,
    WorkstationCaptureConfig,
)

__all__ = [
    "WorkstationCaptureConfig",
    "ArchivalStorageNode",
    "KioskDisplayProfile",
    "SyncStatus",
    "DigitizationWorkstation",
    "ArchivalStorageServer",
    "KioskDisplayController",
]
