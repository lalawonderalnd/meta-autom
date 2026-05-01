"""Optional OCR helper for reading text from screens."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from accfarm_device.device import Device

logger = logging.getLogger(__name__)


class OcrService:
    """OCR service for reading text from screenshots."""

    def __init__(self, engine: str = "tesseract"):
        """
        Initialize OCR service.

        Args:
            engine: OCR engine to use ("tesseract" or "paddle")
        """
        self._engine = engine
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Lazy initialization of OCR engine."""
        if self._initialized:
            return

        if self._engine == "tesseract":
            try:
                import pytesseract
                self._ocr = pytesseract
                self._initialized = True
            except ImportError:
                logger.warning("pytesseract not installed, OCR disabled")
        elif self._engine == "paddle":
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(use_angle_cls=True, lang="en")
                self._initialized = True
            except ImportError:
                logger.warning("paddleocr not installed, OCR disabled")

    def extract_text(self, image_bytes: bytes) -> str:
        """
        Extract text from an image.

        Args:
            image_bytes: PNG/JPEG image bytes

        Returns:
            Extracted text string
        """
        self._ensure_initialized()

        if not self._initialized:
            return ""

        try:
            from PIL import Image
            import io

            img = Image.open(io.BytesIO(image_bytes))

            if self._engine == "tesseract":
                text = self._ocr.image_to_string(img)
                return text.strip()
            elif self._engine == "paddle":
                import numpy as np
                img_array = np.array(img)
                result = self._ocr.ocr(img_array, cls=True)
                if result and result[0]:
                    texts = [line[1][0] for line in result[0] if line]
                    return "\n".join(texts)

        except Exception as e:
            logger.error("OCR failed", extra={"error": str(e)})

        return ""

    def find_text_region(
        self,
        image_bytes: bytes,
        search_text: str,
        threshold: float = 0.8,
    ) -> tuple[int, int, int, int] | None:
        """
        Find the bounding box of specific text in an image.

        Args:
            image_bytes: PNG/JPEG image bytes
            search_text: Text to search for
            threshold: Similarity threshold (0-1)

        Returns:
            Bounding box (left, top, right, bottom) or None if not found
        """
        self._ensure_initialized()

        if not self._initialized:
            return None

        try:
            from PIL import Image
            import io

            img = Image.open(io.BytesIO(image_bytes))

            if self._engine == "paddle":
                import numpy as np
                img_array = np.array(img)
                result = self._ocr.ocr(img_array, cls=True)

                if result and result[0]:
                    for line in result[0]:
                        if line:
                            detected_text = line[1][0]
                            bbox = line[0]  # Four corners

                            # Check similarity
                            if self._text_similarity(detected_text, search_text) >= threshold:
                                # Convert corners to rect
                                xs = [p[0] for p in bbox]
                                ys = [p[1] for p in bbox]
                                return (min(xs), min(ys), max(xs), max(ys))

            elif self._engine == "tesseract":
                # Tesseract with pytesseract can give box data
                import pytesseract
                boxes = pytesseract.image_to_boxes(img)
                width, height = img.size

                for box in boxes.splitlines():
                    parts = box.split()
                    char = parts[0]
                    left = int(parts[1])
                    bottom = int(parts[2])
                    right = int(parts[3])
                    top = int(parts[4])

                    # Simple character-level matching
                    if search_text.lower() in char.lower():
                        # Convert to PIL coordinates
                        return (
                            left,
                            height - bottom,
                            right,
                            height - top,
                        )

        except Exception as e:
            logger.error("Text region search failed", extra={"error": str(e)})

        return None

    def _text_similarity(self, a: str, b: str) -> float:
        """Calculate simple text similarity ratio."""
        a_lower = a.lower().strip()
        b_lower = b.lower().strip()

        if a_lower == b_lower:
            return 1.0

        if b_lower in a_lower:
            return 0.9

        # Simple Levenshtein-like check
        longer = a_lower if len(a_lower) > len(b_lower) else b_lower
        shorter = a_lower if len(a_lower) <= len(b_lower) else b_lower

        if len(longer) == 0:
            return 1.0

        distance = sum(1 for i in range(len(shorter)) if shorter[i] != longer[i])
        distance += abs(len(longer) - len(shorter))

        return 1.0 - (distance / len(longer))

    def read_ig_version(self, screenshot_bytes: bytes) -> str | None:
        """
        Read Instagram version from a screenshot.

        Looks for version text in typical IG settings screen locations.

        Args:
            screenshot_bytes: Screenshot PNG bytes

        Returns:
            Version string or None
        """
        text = self.extract_text(screenshot_bytes)

        # Look for version patterns like "Version 123.0.0.12.123"
        import re

        patterns = [
            r"Version\s+([\d.]+)",
            r"v([\d.]+)",
            r"Instagram\s+([\d.]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None
