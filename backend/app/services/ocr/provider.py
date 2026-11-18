from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image

import pytesseract
from app.core.config import settings


class OCRProvider(ABC):
    @abstractmethod
    def extract_text(self, image_path: str) -> str:
        """Extracts raw text from image file."""
        pass


class TesseractOCRProvider(OCRProvider):
    def __init__(self, tesseract_cmd: str | None = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        elif settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    def extract_text(self, image_path: str) -> str:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found at {image_path}")

        image = Image.open(path)
        # Use psm 6 (assume a single uniform block of text) or default
        text = pytesseract.image_to_string(image, config="--psm 6")
        return text.strip()


class FallbackOCRProvider(OCRProvider):
    """Graceful fallback provider when external OCR engine is unavailable or unconfigured."""

    def extract_text(self, image_path: str) -> str:
        return ""


def get_ocr_provider() -> OCRProvider:
    try:
        provider = TesseractOCRProvider()
        return provider
    except Exception:
        return FallbackOCRProvider()
