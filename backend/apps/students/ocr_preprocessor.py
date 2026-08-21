import io
import math
from typing import List, Tuple, Optional
import numpy as np
from PIL import Image, ImageOps
import cv2
import pymupdf  # PyMuPDF

# Strict resource limits
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_DIMENSION = 4000          # 4000x4000 px
MAX_PDF_PAGES = 3                   # Max 3 pages
PDF_RENDER_DPI = 180                # Optimal DPI for OCR clarity & speed


class PreprocessError(Exception):
    pass


def deskew_image(image_np: np.ndarray) -> np.ndarray:
    """
    Detects skew angle in document and rotates the image back to horizontal.
    """
    try:
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY) if len(image_np.shape) == 3 else image_np
        # Invert and threshold
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 4
        )

        # Find non-zero points (text pixels)
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) < 100:
            return image_np

        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle
        else:
            angle = -angle

        # If angle is negligible (< 0.5 degrees), avoid rotation
        if abs(angle) < 0.5 or abs(angle) > 45:
            return image_np

        (h, w) = image_np.shape[:2]
        center = (w // 2, h // 2)
        m = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image_np, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )
        return rotated
    except Exception:
        return image_np


def enhance_contrast(image_np: np.ndarray) -> np.ndarray:
    """
    Applies CLAHE (Contrast Limited Adaptive Histogram Equalization)
    to boost readability of faded ink, light text, and dark shadows.
    """
    try:
        if len(image_np.shape) == 3:
            # Convert to LAB color space
            lab = cv2.cvtColor(image_np, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            limg = cv2.merge((cl, a, b))
            return cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
        else:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(image_np)
    except Exception:
        return image_np


def prepare_document_images(
    file_bytes: bytes, filename: str = '', max_pages: int = MAX_PDF_PAGES, dpi: int = PDF_RENDER_DPI
) -> List[np.ndarray]:
    """
    Converts uploaded file bytes (PDF or Image) into a list of preprocessed RGB numpy arrays.
    Runs 100% in RAM memory. Enforces strict size and dimension checks.
    """
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise PreprocessError(f"File size exceeds maximum allowed limit of {MAX_UPLOAD_BYTES // (1024 * 1024)}MB.")

    if not file_bytes:
        raise PreprocessError("Uploaded file is empty.")

    is_pdf = filename.lower().endswith('.pdf') or file_bytes.startswith(b'%PDF')
    processed_images: List[np.ndarray] = []

    if is_pdf:
        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            num_pages = min(len(doc), max_pages)
            if num_pages == 0:
                raise PreprocessError("PDF contains no readable pages.")

            for page_num in range(num_pages):
                page = doc[page_num]
                # Render page at requested DPI
                pix = page.get_pixmap(dpi=dpi)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Validate dimensions
                if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
                    img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)

                img_np = np.array(img)
                # Preprocess: deskew & enhance
                deskewed = deskew_image(img_np)
                enhanced = enhance_contrast(deskewed)
                processed_images.append(enhanced)
            doc.close()
        except Exception as e:
            if isinstance(e, PreprocessError):
                raise
            raise PreprocessError(f"Failed to parse PDF document: {str(e)}")
    else:
        # Standard Image file
        try:
            with Image.open(io.BytesIO(file_bytes)) as pil_img:
                # Handle EXIF orientation if present
                pil_img = ImageOps.exif_transpose(pil_img)
                rgb_img = pil_img.convert("RGB")

                # Validate dimensions
                if rgb_img.width > MAX_IMAGE_DIMENSION or rgb_img.height > MAX_IMAGE_DIMENSION:
                    rgb_img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)

                img_np = np.array(rgb_img)
                deskewed = deskew_image(img_np)
                enhanced = enhance_contrast(deskewed)
                processed_images.append(enhanced)
        except Exception as e:
            raise PreprocessError(f"Corrupted or unsupported image file: {str(e)}")

    return processed_images
