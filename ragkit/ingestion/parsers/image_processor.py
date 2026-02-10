"""Image extraction utilities for advanced parsing."""

from __future__ import annotations

import logging
from typing import Any

from ragkit.config.schema_v2 import DocumentParsingConfig

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Extracts images from PDF pages and generates captions."""

    def __init__(self, config: DocumentParsingConfig) -> None:
        self.config = config
        self._caption_model = None
        self._caption_processor = None

    async def extract_images(self, page: Any, page_num: int) -> list[dict[str, Any]]:
        """Extract images from a pdfplumber page.

        pdfplumber exposes image metadata but not raw bytes. We return the
        metadata so downstream processors can optionally re-extract via a
        dedicated PDF library (e.g., PyMuPDF).
        """
        images: list[dict[str, Any]] = []

        if not hasattr(page, "images"):
            return images

        for idx, image in enumerate(page.images):
            images.append(
                {
                    "page_number": page_num,
                    "index": idx,
                    "bbox": image.get("bbox"),
                    "width": image.get("width"),
                    "height": image.get("height"),
                    "object_id": image.get("object_id"),
                    "data": None,
                }
            )

        return images

    async def generate_caption(self, image_data: bytes) -> str:
        """Generate a caption for an image using a vision model."""
        if not image_data:
            return ""

        if self._caption_model is None:
            try:
                from transformers import BlipForConditionalGeneration, BlipProcessor
            except Exception as exc:  # noqa: BLE001
                logger.warning("Image captioning dependencies missing: %s", exc)
                return ""

            model_name = self.config.image_captioning_model or "blip-base"
            self._caption_processor = BlipProcessor.from_pretrained(model_name)
            self._caption_model = BlipForConditionalGeneration.from_pretrained(model_name)

        try:
            import io

            from PIL import Image
        except Exception as exc:  # noqa: BLE001
            logger.warning("Pillow not available for captioning: %s", exc)
            return ""

        try:
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load image for captioning: %s", exc)
            return ""

        inputs = self._caption_processor(image, return_tensors="pt")
        output = self._caption_model.generate(**inputs, max_new_tokens=30)
        caption = self._caption_processor.decode(output[0], skip_special_tokens=True)
        return caption
