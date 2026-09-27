"""Unit tests for Preprocessing Filters and PreprocessingPipeline (Requirement R4)."""

from pathlib import Path
import cv2
import numpy as np
import pytest
from PIL import Image

from sih_archive.preprocessing.filters import (
    CLAHEFilter,
    DenoiseFilter,
    DeskewFilter,
    GrayscaleFilter,
    PreprocessingFilter,
    PreprocessingPipeline,
    ResizeFilter,
    ThresholdFilter,
)


@pytest.fixture
def synthetic_color_image() -> np.ndarray:
    """Creates a 100x150 synthetic RGB color image with text-like shapes."""
    img = np.ones((100, 150, 3), dtype=np.uint8) * 240
    # Add colored rectangle
    img[20:80, 30:120] = [180, 120, 50]
    return img


@pytest.fixture
def synthetic_gray_image() -> np.ndarray:
    """Creates a 100x150 synthetic grayscale image."""
    img = np.ones((100, 150), dtype=np.uint8) * 240
    # Add dark text-like strokes
    img[40:60, 20:130] = 30
    return img


def test_grayscale_filter_from_rgb(synthetic_color_image: np.ndarray):
    """Verify GrayscaleFilter converts 3-channel RGB to 2D single-channel image."""
    f = GrayscaleFilter(color_format="RGB")
    assert f.name == "grayscale"
    out = f.apply(synthetic_color_image)
    assert out.ndim == 2
    assert out.shape == (100, 150)
    assert out.dtype == np.uint8
    meta = f.get_metadata()
    assert meta["channels_in"] == 3
    assert meta["channels_out"] == 1


def test_grayscale_filter_already_gray(synthetic_gray_image: np.ndarray):
    """Verify GrayscaleFilter returns unchanged array if already 2D."""
    f = GrayscaleFilter()
    out = f.apply(synthetic_gray_image)
    assert out.ndim == 2
    assert np.array_equal(out, synthetic_gray_image)
    meta = f.get_metadata()
    assert meta["channels_in"] == 1


def test_resize_filter_scale_factor(synthetic_gray_image: np.ndarray):
    """Verify ResizeFilter rescales dimensions proportionally."""
    f = ResizeFilter(scale_factor=2.0, interpolation="cubic")
    assert f.name == "resize"
    out = f.apply(synthetic_gray_image)
    assert out.shape == (200, 300)
    meta = f.get_metadata()
    assert meta["scale_factor"] == 2.0
    assert meta["interpolation"] == "cubic"
    assert meta["output_shape"] == [200, 300]


def test_resize_filter_explicit_dimensions(synthetic_gray_image: np.ndarray):
    """Verify ResizeFilter resizes to explicit target width and height."""
    f = ResizeFilter(target_width=80, target_height=60)
    out = f.apply(synthetic_gray_image)
    assert out.shape == (60, 80)
    meta = f.get_metadata()
    assert meta["target_width"] == 80
    assert meta["target_height"] == 60


def test_resize_filter_invalid_args():
    """Verify validation on invalid resize parameters."""
    with pytest.raises(ValueError):
        ResizeFilter(scale_factor=-1.0)
    with pytest.raises(ValueError):
        ResizeFilter(interpolation="unsupported_interp")


def test_clahe_filter_grayscale(synthetic_gray_image: np.ndarray):
    """Verify CLAHEFilter applies local contrast enhancement on grayscale image."""
    f = CLAHEFilter(clip_limit=3.0, tile_grid_size=(4, 4))
    assert f.name == "clahe"
    out = f.apply(synthetic_gray_image)
    assert out.shape == synthetic_gray_image.shape
    assert out.dtype == np.uint8
    meta = f.get_metadata()
    assert meta["clip_limit"] == 3.0
    assert meta["tile_grid_size"] == [4, 4]


def test_clahe_filter_color(synthetic_color_image: np.ndarray):
    """Verify CLAHEFilter normalizes L-channel in LAB space for color images."""
    f = CLAHEFilter(clip_limit=2.0)
    out = f.apply(synthetic_color_image)
    assert out.shape == synthetic_color_image.shape
    assert out.ndim == 3


def test_threshold_filter_otsu(synthetic_gray_image: np.ndarray):
    """Verify ThresholdFilter with Otsu creates pure binary image (0 or 255)."""
    f = ThresholdFilter(method="otsu")
    assert f.name == "threshold"
    out = f.apply(synthetic_gray_image)
    assert out.shape == synthetic_gray_image.shape
    unique_vals = set(np.unique(out))
    assert unique_vals.issubset({0, 255})
    meta = f.get_metadata()
    assert meta["method"] == "otsu"
    assert meta["computed_threshold"] is not None


def test_threshold_filter_adaptive_methods(synthetic_gray_image: np.ndarray):
    """Verify ThresholdFilter with adaptive Gaussian and Mean binarization."""
    f_gauss = ThresholdFilter(method="adaptive_gaussian", block_size=11, c=2.0)
    out_g = f_gauss.apply(synthetic_gray_image)
    assert set(np.unique(out_g)).issubset({0, 255})

    f_mean = ThresholdFilter(method="adaptive_mean", block_size=11, c=2.0)
    out_m = f_mean.apply(synthetic_gray_image)
    assert set(np.unique(out_m)).issubset({0, 255})


def test_threshold_filter_validation():
    """Verify error handling on invalid threshold parameters."""
    with pytest.raises(ValueError):
        ThresholdFilter(method="invalid_method")
    with pytest.raises(ValueError):
        ThresholdFilter(block_size=4)  # Even block size must be rejected


def test_deskew_filter_zero_angle(synthetic_gray_image: np.ndarray):
    """Verify DeskewFilter leaves unrotated image unchanged."""
    f = DeskewFilter(max_angle=45.0)
    assert f.name == "deskew"
    out = f.apply(synthetic_gray_image)
    assert out.shape == synthetic_gray_image.shape
    meta = f.get_metadata()
    assert abs(meta["detected_angle"]) < 1.0


def test_deskew_filter_detection_and_warp():
    """Verify DeskewFilter detects rotation and applies correction."""
    canvas = np.ones((300, 300), dtype=np.uint8) * 255
    cv2.putText(canvas, "DR BABASAHEB AMBEDKAR", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 0, 2)

    # Artificially rotate by 4 degrees
    center = (150, 150)
    M = cv2.getRotationMatrix2D(center, 4.0, 1.0)
    rotated = cv2.warpAffine(canvas, M, (300, 300), borderValue=255)

    f = DeskewFilter(max_angle=45.0)
    deskewed = f.apply(rotated)
    meta = f.get_metadata()

    assert meta["applied"] is True
    assert abs(meta["detected_angle"] - (-4.0)) < 1.0 or abs(meta["detected_angle"] - 4.0) < 1.0
    assert deskewed.shape == (300, 300)


def test_denoise_filter_methods(synthetic_gray_image: np.ndarray):
    """Verify DenoiseFilter methods: fast_nl_means, bilateral, median, gaussian."""
    for method in ("fast_nl_means", "bilateral", "median", "gaussian"):
        f = DenoiseFilter(method=method)
        assert f.name == "denoise"
        out = f.apply(synthetic_gray_image)
        assert out.shape == synthetic_gray_image.shape
        meta = f.get_metadata()
        assert meta["method"] == method


def test_preprocessing_pipeline_sequential(synthetic_color_image: np.ndarray):
    """Verify PreprocessingPipeline executes chained filters sequentially with telemetry."""
    pipeline = PreprocessingPipeline(
        filters=[
            GrayscaleFilter(),
            CLAHEFilter(clip_limit=2.0),
            ThresholdFilter(method="otsu"),
        ],
        name="custom_test",
    )
    processed, meta = pipeline.apply(synthetic_color_image)

    assert processed.ndim == 2
    assert set(np.unique(processed)).issubset({0, 255})
    assert meta["pipeline"] == "custom_test"
    assert meta["filter_names"] == ["grayscale", "clahe", "threshold"]
    assert len(meta["filters"]) == 3
    assert meta["duration_ms"] >= 0.0
    assert meta["input_dimensions"] == [100, 150, 3]
    assert meta["output_dimensions"] == [100, 150]


def test_preprocessing_pipeline_from_spec():
    """Verify PreprocessingPipeline.from_spec parses string specs and aliases."""
    raw_p = PreprocessingPipeline.from_spec("raw")
    assert len(raw_p.filters) == 0

    otsu_p = PreprocessingPipeline.from_spec("otsu")
    assert [f.name for f in otsu_p.filters] == ["threshold"]

    comp_p = PreprocessingPipeline.from_spec("grayscale,clahe,otsu")
    assert [f.name for f in comp_p.filters] == ["grayscale", "clahe", "threshold"]

    std_p = PreprocessingPipeline.from_spec("standard")
    assert len(std_p.filters) == 5


def test_preprocessing_pipeline_process_file(tmp_path: Path):
    """Verify PreprocessingPipeline.process_file reads and writes images correctly."""
    input_file = tmp_path / "test_page.png"
    output_file = tmp_path / "processed_page.png"

    # Create dummy image
    im = Image.new("RGB", (120, 80), color=(220, 200, 180))
    im.save(input_file)

    pipeline = PreprocessingPipeline.from_spec("grayscale,otsu")
    arr, meta, res_path = pipeline.process_file(input_file, output_path=output_file)

    assert res_path == output_file
    assert output_file.is_file()
    assert arr.shape == (80, 120)
    assert meta["filter_names"] == ["grayscale", "threshold"]
