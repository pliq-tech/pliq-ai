"""Fraud detection models for image and listing analysis."""

import io
import math
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ExifTags


@dataclass
class ELAResult:
    score: float
    details: str
    heatmap_bytes: bytes | None = None


@dataclass
class FFTResult:
    score: float
    detected_patterns: list[str] = field(default_factory=list)
    details: str = ""


@dataclass
class EXIFResult:
    score: float
    metadata: dict = field(default_factory=dict)
    anomalies: list[str] = field(default_factory=list)
    details: str = ""


@dataclass
class FraudReport:
    overall_score: float
    ela_result: ELAResult | None = None
    fft_result: FFTResult | None = None
    exif_result: EXIFResult | None = None
    explanation: str = ""


@dataclass
class PriceAnomalyReport:
    score: float
    confidence: float
    z_score: float
    median_price: float
    comparable_count: int
    explanation: str = ""


class ELAAnalyzer:
    """Error Level Analysis for image manipulation detection."""

    def __init__(self, quality: int = 95, amplification: float = 15.0):
        self.quality = quality
        self.amplification = amplification

    def analyze(self, image_bytes: bytes) -> ELAResult:
        try:
            original = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception:
            return ELAResult(score=0.0, details="Failed to load image")

        # Re-save at known quality
        buffer = io.BytesIO()
        original.save(buffer, "JPEG", quality=self.quality)
        buffer.seek(0)
        resaved = Image.open(buffer).convert("RGB")

        # Compute pixel-wise difference
        orig_arr = np.array(original, dtype=np.float32)
        resaved_arr = np.array(resaved, dtype=np.float32)
        diff = np.abs(orig_arr - resaved_arr)

        # Amplify differences
        amplified = np.clip(diff * self.amplification, 0, 255).astype(np.uint8)

        # Compute score: higher variance in ELA = more likely manipulated
        mean_diff = float(np.mean(diff))
        std_diff = float(np.std(diff))
        max_diff = float(np.max(diff))

        # Normalize score to 0-1 range
        score = min(1.0, (std_diff / 30.0))

        # Generate heatmap
        heatmap_img = Image.fromarray(amplified)
        heatmap_buffer = io.BytesIO()
        heatmap_img.save(heatmap_buffer, "PNG")

        return ELAResult(
            score=score,
            details=f"Mean diff: {mean_diff:.2f}, Std: {std_diff:.2f}, Max: {max_diff:.2f}",
            heatmap_bytes=heatmap_buffer.getvalue(),
        )


class FFTAnalyzer:
    """FFT-based copy-paste and pattern detection."""

    def analyze(self, image_bytes: bytes) -> FFTResult:
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("L")
        except Exception:
            return FFTResult(score=0.0, details="Failed to load image")

        arr = np.array(img, dtype=np.float32)

        # 2D FFT
        fft = np.fft.fft2(arr)
        fft_shifted = np.fft.fftshift(fft)
        magnitude = np.log1p(np.abs(fft_shifted))

        # Detect peaks (values > 3 std above mean)
        mean_mag = float(np.mean(magnitude))
        std_mag = float(np.std(magnitude))
        threshold = mean_mag + 3 * std_mag

        peaks = np.argwhere(magnitude > threshold)
        center = np.array(magnitude.shape) / 2

        # Filter out DC component (center)
        patterns = []
        for peak in peaks:
            dist = np.sqrt(np.sum((peak - center) ** 2))
            if dist > 5:  # Ignore center region
                patterns.append(f"Peak at offset ({peak[0]-int(center[0])}, {peak[1]-int(center[1])})")

        score = min(1.0, len(patterns) / 20.0)

        return FFTResult(
            score=score,
            detected_patterns=patterns[:10],
            details=f"Found {len(patterns)} frequency peaks above threshold",
        )


class EXIFAnalyzer:
    """EXIF metadata anomaly detection."""

    MANIPULATION_SOFTWARE = {
        "photoshop", "gimp", "lightroom", "snapseed", "pixlr",
        "afterlight", "faceapp", "facetune",
    }

    def analyze(self, image_bytes: bytes) -> EXIFResult:
        try:
            img = Image.open(io.BytesIO(image_bytes))
        except Exception:
            return EXIFResult(score=0.0, details="Failed to load image")

        exif_data = img.getexif()
        anomalies: list[str] = []
        metadata: dict = {}
        score = 0.0

        if not exif_data:
            if img.format == "JPEG":
                score += 0.3
                anomalies.append("Missing EXIF on JPEG image")
            return EXIFResult(
                score=min(score, 1.0),
                metadata=metadata,
                anomalies=anomalies,
                details="No EXIF data found",
            )

        # Extract readable EXIF
        for tag_id, value in exif_data.items():
            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
            metadata[tag_name] = str(value)

        # Check for manipulation software
        software = metadata.get("Software", "").lower()
        for tool in self.MANIPULATION_SOFTWARE:
            if tool in software:
                score += 0.5
                anomalies.append(f"Editing software detected: {metadata.get('Software')}")
                break

        return EXIFResult(
            score=min(score, 1.0),
            metadata=metadata,
            anomalies=anomalies,
            details=f"Analyzed {len(metadata)} EXIF fields, found {len(anomalies)} anomalies",
        )


class FraudScoreAggregator:
    """Combines individual fraud detection scores into an overall score."""

    def __init__(
        self,
        ela_weight: float = 0.35,
        fft_weight: float = 0.25,
        exif_weight: float = 0.20,
        reverse_weight: float = 0.20,
    ):
        self.ela_weight = ela_weight
        self.fft_weight = fft_weight
        self.exif_weight = exif_weight
        self.reverse_weight = reverse_weight

    def aggregate(
        self,
        ela: ELAResult | None = None,
        fft: FFTResult | None = None,
        exif: EXIFResult | None = None,
        reverse_score: float = 0.0,
    ) -> FraudReport:
        ela_score = ela.score if ela else 0.0
        fft_score = fft.score if fft else 0.0
        exif_score = exif.score if exif else 0.0

        overall = (
            ela_score * self.ela_weight
            + fft_score * self.fft_weight
            + exif_score * self.exif_weight
            + reverse_score * self.reverse_weight
        )

        return FraudReport(
            overall_score=overall,
            ela_result=ela,
            fft_result=fft,
            exif_result=exif,
        )


class PriceAnomalyDetector:
    """Detects price anomalies using statistical comparison."""

    def detect(
        self,
        listing_price: float,
        comparable_prices: list[float],
    ) -> PriceAnomalyReport:
        if not comparable_prices:
            return PriceAnomalyReport(
                score=0.0,
                confidence=0.0,
                z_score=0.0,
                median_price=0.0,
                comparable_count=0,
                explanation="No comparable listings available",
            )

        median = float(np.median(comparable_prices))
        std_dev = float(np.std(comparable_prices)) if len(comparable_prices) > 1 else median * 0.1

        if std_dev == 0:
            std_dev = median * 0.1

        z_score = (listing_price - median) / std_dev

        # Sigmoid scoring: extreme z-scores → high anomaly score
        raw_score = 1.0 / (1.0 + math.exp(-abs(z_score) + 2))

        # Confidence scales with comparable count
        confidence = min(1.0, len(comparable_prices) / 10.0)

        score = raw_score * confidence

        direction = "below" if z_score < 0 else "above"

        return PriceAnomalyReport(
            score=score,
            confidence=confidence,
            z_score=z_score,
            median_price=median,
            comparable_count=len(comparable_prices),
            explanation=f"Price is {abs(z_score):.1f} std devs {direction} median ({median:.0f})",
        )


