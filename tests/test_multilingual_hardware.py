"""
Tests for Multilingual (E4) and Hardware (E5) Interfaces and Schemas.
"""

from sih_archive.hardware.schemas import (
    ArchivalStorageNode,
    KioskDisplayProfile,
    SyncStatus,
    WorkstationCaptureConfig,
)
from sih_archive.multilingual.base import MockTTSAdapter, MockTranslationAdapter
from sih_archive.multilingual.schemas import TranslationRecord


def test_translation_adapter_and_provenance():
    adapter = MockTranslationAdapter()
    res = adapter.translate(
        text="Castes in India",
        source_lang="eng",
        target_lang="hin",
        source_page_id="doc_p0001",
    )
    assert isinstance(res, TranslationRecord)
    assert res.source_lang == "eng"
    assert res.target_lang == "hin"
    assert res.source_page_id == "doc_p0001"
    assert not res.is_human_verified
    assert "[HIN_TRANSLATION]" in res.translated_text


def test_tts_adapter_and_duration():
    adapter = MockTTSAdapter()
    res = adapter.synthesize_speech(
        text="Democracy is not merely a form of government.",
        language="eng",
        source_page_id="doc_p0002",
        output_audio_path="outputs/audio/sample.wav",
    )
    assert res.duration_seconds > 0.0
    assert res.source_page_id == "doc_p0002"
    assert res.audio_path == "outputs/audio/sample.wav"


def test_hardware_schemas():
    workstation = WorkstationCaptureConfig(target_dpi=400, color_mode="rgb24")
    assert workstation.target_dpi == 400

    node = ArchivalStorageNode(node_id="node_01", mount_point="/mnt/archive")
    assert node.is_read_only

    kiosk = KioskDisplayProfile(kiosk_id="kiosk_gallery_1", resolution=[1920, 1080])
    assert kiosk.touch_enabled
    assert kiosk.resolution == [1920, 1080]

    sync = SyncStatus(state="idle", pending_items_count=0)
    assert sync.state == "idle"
