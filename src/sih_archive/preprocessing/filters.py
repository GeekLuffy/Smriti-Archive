"""
Image preprocessing filters and execution pipeline for archival documents (Requirement R4).

Provides modular, configurable transformations to evaluate whether preprocessing
objectively improves or degrades OCR accuracy on historical scans.
"""

from abc import ABC, abstractmethod
from pathlib import Path
import time
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
import cv2
import numpy as np
from PIL import Image


class PreprocessingFilter(ABC):
    """Abstract interface for modular image preprocessing filters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier of the preprocessing filter."""
        pass

    @abstractmethod
    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        Applies transformation to an image array.

        Parameters:
            image: NumPy ndarray (RGB or Grayscale uint8).

        Returns:
            Processed NumPy ndarray.
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Returns deterministic parameter metadata for provenance tracking."""
        pass


class GrayscaleFilter(PreprocessingFilter):
    """Converts multi-channel color images to single-channel 8-bit luminance."""

    def __init__(self, color_format: str = "RGB"):
        """
        Parameters:
            color_format: Source channel ordering, 'RGB' or 'BGR'.
        """
        self._color_format = color_format.upper()
        self._last_channels_in = 3

    @property
    def name(self) -> str:
        return "grayscale"

    def apply(self, image: np.ndarray) -> np.ndarray:
        if image is None:
            raise ValueError("Input image cannot be None.")

        if image.ndim == 2:
            self._last_channels_in = 1
            return image

        if image.ndim == 3 and image.shape[2] == 1:
            self._last_channels_in = 1
            return image[:, :, 0]

        self._last_channels_in = image.shape[2]
        if self._color_format == "BGR":
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "channels_in": self._last_channels_in,
            "channels_out": 1,
            "color_format": self._color_format,
        }


class ResizeFilter(PreprocessingFilter):
    """Rescales image dimensions for DPI normalization or character height optimization."""

    INTERPOLATION_MAP = {
        "cubic": cv2.INTER_CUBIC,
        "linear": cv2.INTER_LINEAR,
        "area": cv2.INTER_AREA,
        "nearest": cv2.INTER_NEAREST,
        "lanczos": cv2.INTER_LANCZOS4,
    }

    def __init__(
        self,
        scale_factor: float = 1.0,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
        interpolation: str = "cubic",
    ):
        """
        Parameters:
            scale_factor: Multiplier for image width and height.
            target_width: Explicit output width in pixels (overrides scale_factor if target_height is also set).
            target_height: Explicit output height in pixels.
            interpolation: 'cubic', 'linear', 'area', 'nearest', or 'lanczos'.
        """
        if scale_factor <= 0:
            raise ValueError(f"scale_factor must be positive, got {scale_factor}")
        self.scale_factor = float(scale_factor)
        self.target_width = target_width
        self.target_height = target_height
        interp_lower = interpolation.lower()
        if interp_lower not in self.INTERPOLATION_MAP:
            raise ValueError(
                f"Unsupported interpolation '{interpolation}'. Supported: {list(self.INTERPOLATION_MAP.keys())}"
            )
        self.interpolation = interp_lower
        self._last_input_shape: Optional[Tuple[int, ...]] = None
        self._last_output_shape: Optional[Tuple[int, ...]] = None

    @property
    def name(self) -> str:
        return "resize"

    def apply(self, image: np.ndarray) -> np.ndarray:
        if image is None:
            raise ValueError("Input image cannot be None.")
        self._last_input_shape = image.shape
        interp_flag = self.INTERPOLATION_MAP[self.interpolation]

        if self.target_width is not None and self.target_height is not None:
            resized = cv2.resize(image, (self.target_width, self.target_height), interpolation=interp_flag)
        elif self.scale_factor != 1.0:
            resized = cv2.resize(image, None, fx=self.scale_factor, fy=self.scale_factor, interpolation=interp_flag)
        else:
            resized = image

        self._last_output_shape = resized.shape
        return resized

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "scale_factor": self.scale_factor,
            "target_width": self.target_width,
            "target_height": self.target_height,
            "interpolation": self.interpolation,
            "input_shape": list(self._last_input_shape) if self._last_input_shape else None,
            "output_shape": list(self._last_output_shape) if self._last_output_shape else None,
        }


class CLAHEFilter(PreprocessingFilter):
    """Contrast Limited Adaptive Histogram Equalization for local illumination normalization."""

    def __init__(self, clip_limit: float = 2.0, tile_grid_size: Tuple[int, int] = (8, 8)):
        """
        Parameters:
            clip_limit: Threshold for contrast limiting (typical range 1.0 - 4.0).
            tile_grid_size: Grid dimensions for contextual regions (e.g. (8, 8)).
        """
        if clip_limit <= 0:
            raise ValueError(f"clip_limit must be positive, got {clip_limit}")
        if len(tile_grid_size) != 2 or any(x <= 0 for x in tile_grid_size):
            raise ValueError(f"tile_grid_size must be a pair of positive integers, got {tile_grid_size}")
        self.clip_limit = float(clip_limit)
        self.tile_grid_size = (int(tile_grid_size[0]), int(tile_grid_size[1]))

    @property
    def name(self) -> str:
        return "clahe"

    def apply(self, image: np.ndarray) -> np.ndarray:
        if image is None:
            raise ValueError("Input image cannot be None.")
        clahe = cv2.createCLAHE(clipLimit=self.clip_limit, tileGridSize=self.tile_grid_size)

        if image.ndim == 2:
            return clahe.apply(image)
        elif image.ndim == 3 and image.shape[2] == 1:
            equalized = clahe.apply(image[:, :, 0])
            return equalized[:, :, np.newaxis]
        elif image.ndim == 3 and image.shape[2] >= 3:
            # Process in LAB color space so chromaticity is preserved while lightness is normalized
            lab = cv2.cvtColor(image[:, :, :3], cv2.COLOR_RGB2LAB)
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        return image

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "clip_limit": self.clip_limit,
            "tile_grid_size": list(self.tile_grid_size),
        }


class ThresholdFilter(PreprocessingFilter):
    """
    Binarization filter separating text foreground from paper background.
    Supports Otsu global thresholding and Adaptive Gaussian/Mean thresholding.
    """

    SUPPORTED_METHODS = ("otsu", "adaptive_gaussian", "adaptive_mean")

    def __init__(
        self,
        method: Literal["otsu", "adaptive_gaussian", "adaptive_mean"] = "otsu",
        block_size: int = 11,
        c: float = 2.0,
        invert: bool = False,
    ):
        """
        Parameters:
            method: 'otsu', 'adaptive_gaussian', or 'adaptive_mean'.
            block_size: Neighborhood size for adaptive thresholding (must be odd integer >= 3).
            c: Constant subtracted from the mean or weighted mean in adaptive methods.
            invert: If True, foreground text becomes white (255) on dark background.
        """
        method_lower = method.lower()
        if method_lower not in self.SUPPORTED_METHODS:
            raise ValueError(f"Unsupported threshold method '{method}'. Supported: {self.SUPPORTED_METHODS}")
        if block_size < 3 or block_size % 2 == 0:
            raise ValueError(f"block_size must be an odd integer >= 3, got {block_size}")
        self.method = method_lower
        self.block_size = int(block_size)
        self.c = float(c)
        self.invert = bool(invert)
        self._computed_threshold: Optional[float] = None

    @property
    def name(self) -> str:
        return "threshold"

    def apply(self, image: np.ndarray) -> np.ndarray:
        if image is None:
            raise ValueError("Input image cannot be None.")

        # Ensure single-channel grayscale input
        if image.ndim == 3:
            if image.shape[2] == 1:
                gray = image[:, :, 0]
            else:
                gray = cv2.cvtColor(image[:, :, :3], cv2.COLOR_RGB2GRAY)
        else:
            gray = image

        thresh_flag = cv2.THRESH_BINARY_INV if self.invert else cv2.THRESH_BINARY

        if self.method == "otsu":
            ret, binary = cv2.threshold(gray, 0, 255, thresh_flag + cv2.THRESH_OTSU)
            self._computed_threshold = float(ret)
            return binary
        elif self.method == "adaptive_gaussian":
            self._computed_threshold = None
            return cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, thresh_flag, self.block_size, self.c
            )
        elif self.method == "adaptive_mean":
            self._computed_threshold = None
            return cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, thresh_flag, self.block_size, self.c
            )
        return gray

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "method": self.method,
            "block_size": self.block_size,
            "c": self.c,
            "invert": self.invert,
            "computed_threshold": self._computed_threshold,
        }


class DeskewFilter(PreprocessingFilter):
    """
    Detects skew angle from foreground text orientation and corrects tilt using affine rotation.
    """

    def __init__(self, max_angle: float = 45.0, background_color: int = 255):
        """
        Parameters:
            max_angle: Maximum allowable skew correction angle in degrees.
            background_color: Fill value for rotated borders (default 255 = white).
        """
        if max_angle <= 0 or max_angle > 90:
            raise ValueError(f"max_angle must be in (0, 90], got {max_angle}")
        self.max_angle = float(max_angle)
        self.background_color = background_color
        self._last_angle: float = 0.0
        self._applied: bool = False

    @property
    def name(self) -> str:
        return "deskew"

    def detect_skew_angle(self, image: np.ndarray) -> float:
        """
        Detects document skew angle in degrees using minimum-area bounding box on text pixels.
        """
        if image.ndim == 3:
            gray = cv2.cvtColor(image[:, :, :3], cv2.COLOR_RGB2GRAY)
        else:
            gray = image

        # Invert so text is foreground (>0)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        pts = cv2.findNonZero(thresh)
        if pts is None or len(pts) < 20:
            return 0.0

        rect = cv2.minAreaRect(pts)
        (cx, cy), (w, h), angle = rect

        # Normalize OpenCV minAreaRect angle
        if w < h:
            skew_angle = angle - 90.0
        else:
            skew_angle = angle

        # Standardize angle to closest horizontal tilt
        if skew_angle < -45.0:
            skew_angle += 90.0
        elif skew_angle > 45.0:
            skew_angle -= 90.0

        return float(skew_angle)

    def apply(self, image: np.ndarray) -> np.ndarray:
        if image is None:
            raise ValueError("Input image cannot be None.")

        angle = self.detect_skew_angle(image)
        self._last_angle = angle

        # Only apply rotation if angle is significant and within safety bounds
        if abs(angle) < 0.1 or abs(angle) > self.max_angle:
            self._applied = False
            return image

        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        # To cancel the skew angle, rotate by the skew angle
        rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        bg = (
            (self.background_color, self.background_color, self.background_color)
            if image.ndim == 3
            else self.background_color
        )
        rotated = cv2.warpAffine(
            image,
            rot_matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=bg,
        )
        self._applied = True
        return rotated

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "detected_angle": round(self._last_angle, 3),
            "applied": self._applied,
            "max_angle": self.max_angle,
        }


class DenoiseFilter(PreprocessingFilter):
    """Speckle and noise reduction using FastNLMeans, Bilateral, Median, or Gaussian filtering."""

    SUPPORTED_METHODS = ("fast_nl_means", "bilateral", "median", "gaussian")

    def __init__(
        self,
        method: Literal["fast_nl_means", "bilateral", "median", "gaussian"] = "fast_nl_means",
        h: float = 10.0,
        ksize: int = 3,
        sigma_color: float = 75.0,
        sigma_space: float = 75.0,
    ):
        """
        Parameters:
            method: 'fast_nl_means', 'bilateral', 'median', or 'gaussian'.
            h: Filter strength parameter for FastNLMeans.
            ksize: Kernel size (must be odd integer >= 3) for median and gaussian filters.
            sigma_color: Filter sigma in the color space for bilateral filter.
            sigma_space: Filter sigma in the coordinate space for bilateral filter.
        """
        method_lower = method.lower()
        if method_lower not in self.SUPPORTED_METHODS:
            raise ValueError(f"Unsupported denoise method '{method}'. Supported: {self.SUPPORTED_METHODS}")
        if ksize < 3 or ksize % 2 == 0:
            raise ValueError(f"ksize must be an odd integer >= 3, got {ksize}")
        self.method = method_lower
        self.h = float(h)
        self.ksize = int(ksize)
        self.sigma_color = float(sigma_color)
        self.sigma_space = float(sigma_space)

    @property
    def name(self) -> str:
        return "denoise"

    def apply(self, image: np.ndarray) -> np.ndarray:
        if image is None:
            raise ValueError("Input image cannot be None.")

        if self.method == "fast_nl_means":
            if image.ndim == 2 or (image.ndim == 3 and image.shape[2] == 1):
                img2d = image[:, :, 0] if image.ndim == 3 else image
                return cv2.fastNlMeansDenoising(img2d, None, h=self.h, templateWindowSize=7, searchWindowSize=21)
            return cv2.fastNlMeansDenoisingColored(
                image[:, :, :3], None, h=self.h, hColor=self.h, templateWindowSize=7, searchWindowSize=21
            )
        elif self.method == "bilateral":
            return cv2.bilateralFilter(image, d=9, sigmaColor=self.sigma_color, sigmaSpace=self.sigma_space)
        elif self.method == "median":
            return cv2.medianBlur(image, ksize=self.ksize)
        elif self.method == "gaussian":
            return cv2.GaussianBlur(image, (self.ksize, self.ksize), 0)
        return image

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "method": self.method,
            "parameters": {
                "h": self.h,
                "ksize": self.ksize,
                "sigma_color": self.sigma_color,
                "sigma_space": self.sigma_space,
            },
        }


class PreprocessingPipeline:
    """
    Executes an ordered sequence of PreprocessingFilters, tracking execution duration,
    filter parameter metadata, and dimension transformations.
    """

    def __init__(self, filters: Optional[List[PreprocessingFilter]] = None, name: str = "custom"):
        self.filters: List[PreprocessingFilter] = list(filters) if filters else []
        self.pipeline_name: str = name

    def add_filter(self, filter_obj: PreprocessingFilter) -> "PreprocessingPipeline":
        """Appends a preprocessing filter to the pipeline."""
        self.filters.append(filter_obj)
        return self

    @classmethod
    def from_spec(cls, spec: Union[str, List[Union[str, PreprocessingFilter]]]) -> "PreprocessingPipeline":
        """
        Parses filter specifications into a PreprocessingPipeline.

        Examples of spec:
            - 'raw': empty pipeline (no changes)
            - 'grayscale': [GrayscaleFilter()]
            - 'clahe': [CLAHEFilter()]
            - 'otsu': [GrayscaleFilter(), ThresholdFilter(method='otsu')]
            - 'deskew': [DeskewFilter()]
            - 'denoise': [DenoiseFilter(method='fast_nl_means')]
            - 'grayscale,clahe,otsu': composite sequential pipeline
            - ['grayscale', 'clahe', 'otsu']: list of filter names
        """
        if isinstance(spec, str):
            spec_clean = spec.strip().lower()
            if spec_clean in ("", "raw", "none", "passthrough"):
                return cls(filters=[], name="raw")
            # Check for comma-separated or plus-separated filter sequence
            tokens = [t.strip().lower() for t in spec.replace("+", ",").split(",") if t.strip()]
        elif isinstance(spec, (list, tuple)):
            tokens = list(spec)
        else:
            raise TypeError(f"spec must be str or list of filters/strings, got {type(spec)}")

        pipeline = cls(name=str(spec))
        for item in tokens:
            if isinstance(item, PreprocessingFilter):
                pipeline.add_filter(item)
            elif isinstance(item, str):
                name = item.strip().lower()
                if name in ("raw", "none", "passthrough"):
                    continue
                elif name == "grayscale":
                    pipeline.add_filter(GrayscaleFilter())
                elif name == "resize":
                    pipeline.add_filter(ResizeFilter(scale_factor=1.5))
                elif name == "clahe":
                    pipeline.add_filter(CLAHEFilter())
                elif name in ("otsu", "threshold_otsu"):
                    pipeline.add_filter(ThresholdFilter(method="otsu"))
                elif name in ("adaptive_gaussian", "threshold_adaptive_gaussian"):
                    pipeline.add_filter(ThresholdFilter(method="adaptive_gaussian"))
                elif name in ("adaptive_mean", "threshold_adaptive_mean"):
                    pipeline.add_filter(ThresholdFilter(method="adaptive_mean"))
                elif name == "deskew":
                    pipeline.add_filter(DeskewFilter())
                elif name in ("denoise", "fast_nl_means"):
                    pipeline.add_filter(DenoiseFilter(method="fast_nl_means"))
                elif name == "bilateral":
                    pipeline.add_filter(DenoiseFilter(method="bilateral"))
                elif name == "median":
                    pipeline.add_filter(DenoiseFilter(method="median"))
                elif name == "gaussian":
                    pipeline.add_filter(DenoiseFilter(method="gaussian"))
                elif name in ("standard", "preprocessed"):
                    # Standard historical document preprocessing sequence
                    pipeline.add_filter(DeskewFilter())
                    pipeline.add_filter(GrayscaleFilter())
                    pipeline.add_filter(CLAHEFilter())
                    pipeline.add_filter(DenoiseFilter(method="median"))
                    pipeline.add_filter(ThresholdFilter(method="otsu"))
                else:
                    raise ValueError(f"Unknown filter name in spec: '{item}'")
            else:
                raise TypeError(f"Invalid filter specification item: {item}")

        return pipeline

    def apply(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Applies pipeline sequentially to input image array.

        Returns:
            Tuple of (processed_image, execution_metadata_dict).
        """
        if image is None:
            raise ValueError("Input image cannot be None.")

        start_time = time.perf_counter()
        in_shape = list(image.shape)
        curr_img = image.copy()
        filter_metadata_list: List[Dict[str, Any]] = []

        for f in self.filters:
            curr_img = f.apply(curr_img)
            filter_metadata_list.append(f.get_metadata())

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        out_shape = list(curr_img.shape)

        metadata = {
            "pipeline": self.pipeline_name,
            "filter_names": [f.name for f in self.filters],
            "filters": filter_metadata_list,
            "duration_ms": round(duration_ms, 2),
            "input_dimensions": in_shape,
            "output_dimensions": out_shape,
        }
        return curr_img, metadata

    def process_file(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any], Path]:
        """
        Loads an image from file, applies pipeline, and optionally writes output image.

        Returns:
            Tuple of (processed_image, metadata, output_image_path).
        """
        in_p = Path(input_path)
        if not in_p.is_file():
            raise FileNotFoundError(f"Input image not found: {in_p}")

        # Use PIL to read reliably (handling color profiles) and convert to RGB ndarray
        with Image.open(in_p) as pil_im:
            rgb_im = pil_im.convert("RGB")
            img_arr = np.array(rgb_im)

        processed_arr, metadata = self.apply(img_arr)

        if output_path is not None:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            pil_out = Image.fromarray(processed_arr)
            pil_out.save(out_p)
            result_path = out_p
        else:
            result_path = in_p

        return processed_arr, metadata, result_path
