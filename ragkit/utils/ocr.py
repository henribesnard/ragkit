"""Wrapper for OCR engines (Tesseract, EasyOCR, Doctr)."""

from __future__ import annotations

import logging
from typing import Literal

from PIL import Image

logger = logging.getLogger(__name__)


class OCREngine:
    """Unified wrapper for different OCR backends."""

    def __init__(
        self,
        engine: Literal["tesseract", "easyocr", "doctr"],
        languages: list[str],
        dpi: int = 300,
        preprocessing: bool = True,
    ) -> None:
        self.engine = engine
        self.languages = languages
        self.dpi = dpi
        self.preprocessing = preprocessing
        self._ocr_instance = None

    async def extract_text(self, image: Image.Image) -> tuple[str, float]:
        """Extract text from an image with confidence score."""
        if self._ocr_instance is None:
            self._ocr_instance = self._init_ocr()

        if self.preprocessing:
            image = self._preprocess_image(image)

        if self.engine == "tesseract":
            return await self._ocr_tesseract(image)
        if self.engine == "easyocr":
            return await self._ocr_easyocr(image)
        if self.engine == "doctr":
            return await self._ocr_doctr(image)

        raise RuntimeError(f"Unsupported OCR engine: {self.engine}")

    async def _ocr_tesseract(self, image: Image.Image) -> tuple[str, float]:
        """OCR using Tesseract."""
        try:
            import pytesseract
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("pytesseract is not installed") from exc

        lang = "+".join(self.languages) if self.languages else "eng"
        text = pytesseract.image_to_string(image, lang=lang)

        data = pytesseract.image_to_data(
            image, lang=lang, output_type=pytesseract.Output.DICT
        )
        confidences = [int(conf) for conf in data.get("conf", []) if conf != "-1"]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return text, avg_confidence / 100.0

    async def _ocr_easyocr(self, image: Image.Image) -> tuple[str, float]:
        """OCR using EasyOCR."""
        try:
            import numpy as np
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("numpy is required for EasyOCR") from exc

        if self._ocr_instance is None:
            raise RuntimeError("EasyOCR backend is not initialized")

        image_np = np.array(image)
        results = self._ocr_instance.readtext(image_np)

        text_parts: list[str] = []
        confidences: list[float] = []
        for _, text, confidence in results:
            text_parts.append(text)
            confidences.append(confidence)

        text = "\n".join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        return text, avg_confidence

    async def _ocr_doctr(self, image: Image.Image) -> tuple[str, float]:
        """OCR using Doctr."""
        try:
            import numpy as np
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("numpy is required for Doctr") from exc

        if self._ocr_instance is None:
            raise RuntimeError("Doctr backend is not initialized")

        image_np = np.array(image)
        result = self._ocr_instance([image_np])
        text = result.render()
        return text, 0.9

    def _init_ocr(self):
        """Initialize the OCR backend lazily."""
        if self.engine == "easyocr":
            try:
                import easyocr
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError("easyocr is not installed") from exc
            return easyocr.Reader(self.languages or ["en"])

        if self.engine == "doctr":
            try:
                from doctr.models import ocr_predictor
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError("doctr is not installed") from exc
            return ocr_predictor(pretrained=True)

        return None

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Apply basic preprocessing for OCR."""
        from PIL import ImageEnhance, ImageFilter

        image = image.convert("L")
        image = ImageEnhance.Contrast(image).enhance(2.0)
        image = image.filter(ImageFilter.SHARPEN)
        return image
