from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance, ImageOps


def preprocess_image(input_path: str, output_path: str | None = None) -> str:
    """Preprocesses an image for optimal OCR extraction:
    - Converts to grayscale
    - Auto-orients based on EXIF
    - Enhances contrast
    - Resizes if too small/large
    Returns path to preprocessed image.
    """
    path = Path(input_path)
    if not path.exists():
        return input_path

    out_file = Path(output_path) if output_path else path.parent / f"prep_{path.name}"

    try:
        image = Image.open(path)
        # Handle EXIF rotation
        image = ImageOps.exif_transpose(image)

        # Convert to grayscale
        gray = image.convert("L")

        # Contrast enhancement
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(1.8)

        # Resize if width < 1000px for better character resolution
        w, h = enhanced.size
        if w < 1000:
            scale = 1000 / w
            enhanced = enhanced.resize(
                (int(w * scale), int(h * scale)), Image.Resampling.LANCZOS
            )

        enhanced.save(out_file, format="JPEG", quality=90)
        return str(out_file)
    except Exception:
        # If any preprocessing step fails, gracefully fall back to original image
        return input_path


def compute_perceptual_hash(image_path: str) -> str:
    """Computes a simple average hash (aHash) for image duplicate detection."""
    try:
        image = (
            Image.open(image_path).convert("L").resize((8, 8), Image.Resampling.LANCZOS)
        )
        pixels = np.array(image.getdata())
        avg = pixels.mean()
        diff = pixels > avg
        # Convert boolean array to hex string
        decimal_val = 0
        for index, val in enumerate(diff.flatten()):
            if val:
                decimal_val += 1 << index
        return f"{decimal_val:016x}"
    except Exception:
        return "0000000000000000"
