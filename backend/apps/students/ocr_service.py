import io
import time
import threading
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from paddleocr import PaddleOCR
from rapidocr_onnxruntime import RapidOCR

from .ocr_preprocessor import prepare_document_images, PreprocessError
from .ocr_normalizer import ExtractedField
from .ocr_extractors import (
    DocumentClassifier,
    PassportExtractor,
    DiplomaExtractor,
    ContactScreenshotExtractor,
)


class OCREngineManager:
    """
    Thread-safe Singleton managing the life cycle of the OCR engine.
    Initialized once at Django startup and reused across all requests.
    """
    _instance: Optional['OCREngineManager'] = None
    _lock = threading.Lock()

    def __init__(self):
        self.paddle_ocr: Optional[PaddleOCR] = None
        self.rapid_ocr: Optional[RapidOCR] = None
        self._init_engines()

    def _init_engines(self):
        # 1. Initialize PaddleOCR as primary engine
        try:
            self.paddle_ocr = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)
        except Exception:
            self.paddle_ocr = None

        # 2. Initialize RapidOCR as secondary / fallback engine
        try:
            self.rapid_ocr = RapidOCR()
        except Exception:
            self.rapid_ocr = None

    @classmethod
    def get_instance(cls) -> 'OCREngineManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def run_ocr(self, image_np: np.ndarray) -> Tuple[List[str], List[float], str]:
        """
        Runs OCR on a single preprocessed image numpy array.
        Returns: (ocr_lines, confidence_scores, engine_name)
        """
        lines: List[str] = []
        scores: List[float] = []

        # Try PaddleOCR first
        if self.paddle_ocr is not None:
            try:
                results = self.paddle_ocr.ocr(image_np, cls=False)
                if results and results[0]:
                    for item in results[0]:
                        text = item[1][0].strip()
                        score = float(item[1][1])
                        if text:
                            lines.append(text)
                            scores.append(score)
                    return lines, scores, "PaddleOCR"
            except Exception:
                pass

        # Fallback to RapidOCR
        if self.rapid_ocr is not None:
            try:
                results, _ = self.rapid_ocr(image_np)
                if results:
                    for item in results:
                        text = item[1].strip()
                        score = float(item[2]) if len(item) > 2 else 0.90
                        if text:
                            lines.append(text)
                            scores.append(score)
                    return lines, scores, "RapidOCR"
            except Exception:
                pass

        return lines, scores, "None"


# Concurrency guard: Max 4 concurrent OCR inferences to prevent CPU exhaustion
_CONCURRENCY_LIMIT = 4
_ocr_semaphore = threading.BoundedSemaphore(value=_CONCURRENCY_LIMIT)


def process_document_ephemeral(
    file_bytes: bytes, filename: str = '', debug: bool = False
) -> Dict[str, Any]:
    """
    Main entry point for document extraction.
    Runs 100% in-memory with strict resource and timeout guards.
    """
    start_time = time.time()

    # Step 1: Preprocess Images in RAM
    images = prepare_document_images(file_bytes=file_bytes, filename=filename)
    if not images:
        raise PreprocessError("Failed to extract any readable pages from document.")

    # Step 2: Run OCR under concurrency semaphore
    all_raw_lines: List[str] = []
    all_scores: List[float] = []
    engines_used: List[str] = []

    acquired = _ocr_semaphore.acquire(timeout=10.0)
    if not acquired:
        raise TimeoutError("OCR engine is currently busy with other requests. Please retry in a few seconds.")

    try:
        manager = OCREngineManager.get_instance()
        for img in images:
            lines, scores, engine_name = manager.run_ocr(img)
            all_raw_lines.extend(lines)
            all_scores.extend(scores)
            if engine_name not in engines_used:
                engines_used.append(engine_name)

            # Early stopping check: if we already extracted enough passport lines from page 1, don't waste time on page 2/3
            if len(all_raw_lines) >= 15 and any('<<' in l.replace(' ', '') for l in all_raw_lines):
                break
    finally:
        _ocr_semaphore.release()

    full_ocr_text = "\n".join(all_raw_lines)

    # Step 3: Classify Document
    doc_type = DocumentClassifier.classify(all_raw_lines, full_ocr_text)

    # Step 4: Run Domain-Specific Extractor
    field_details_map: Dict[str, ExtractedField] = {}

    if doc_type in ("PASSPORT", "ID_CARD"):
        field_details_map = PassportExtractor.extract(all_raw_lines, full_ocr_text, all_scores)
    elif doc_type in ("DIPLOMA", "SCHOOL_CERTIFICATE"):
        is_shahodat = (doc_type == "SCHOOL_CERTIFICATE")
        field_details_map = DiplomaExtractor.extract(all_raw_lines, full_ocr_text, is_shahodatnoma=is_shahodat)
    elif doc_type == "CONTACT_SCREENSHOT":
        field_details_map = ContactScreenshotExtractor.extract(all_raw_lines, full_ocr_text)
    else:
        # Unknown fallback: attempt passport first, then contact
        field_details_map = PassportExtractor.extract(all_raw_lines, full_ocr_text, all_scores)
        if not field_details_map:
            field_details_map = ContactScreenshotExtractor.extract(all_raw_lines, full_ocr_text)

    # Flatten fields for backward compatibility
    simple_fields: Dict[str, str] = {k: f.value for k, f in field_details_map.items()}
    serialized_details: Dict[str, Dict[str, Any]] = {k: f.to_dict() for k, f in field_details_map.items()}

    elapsed_ms = int((time.time() - start_time) * 1000)

    response_data = {
        "document_type": doc_type,
        "fields": simple_fields,
        "field_details": serialized_details,
        "metadata": {
            "latency_ms": elapsed_ms,
            "ocr_engine": ", ".join(engines_used) or "None",
            "pages_processed": len(images)
        }
    }

    if debug:
        response_data["ocr_text"] = full_ocr_text

    return response_data
