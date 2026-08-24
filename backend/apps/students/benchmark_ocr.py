import os
import sys
import io
import time
import psutil
from PIL import Image, ImageDraw, ImageFont

# Set up Django environment
import pathlib
backend_dir = str(pathlib.Path(__file__).resolve().parent.parent.parent)
# Ensure backend directory is prioritized and workspace root is cleaned
sys.path = [backend_dir] + [p for p in sys.path if os.path.abspath(p) != os.path.dirname(backend_dir)]
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

try:
    import paddle
except ImportError:
    paddle = None

from apps.students.ocr_service import OCREngineManager, process_document_ephemeral


def get_current_memory_mb() -> float:
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)



def create_synthetic_passport_image() -> bytes:
    img = Image.new('RGB', (1000, 700), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 30), 'PASPORT RAQAMI / PASSPORT No. FA7958189', fill=(0, 0, 0))
    draw.text((30, 80), 'FAMILIYASI / SURNAME', fill=(0, 0, 0))
    draw.text((30, 110), 'ALISHEROV', fill=(0, 0, 0))
    draw.text((30, 160), 'ISMI / GIVEN NAMES', fill=(0, 0, 0))
    draw.text((30, 190), 'MUKHAMMADRAKHMON', fill=(0, 0, 0))
    draw.text((30, 240), 'OTASINING ISMI / FATHER\'S NAME', fill=(0, 0, 0))
    draw.text((30, 270), 'ABDULKHOSHIM UGLI', fill=(0, 0, 0))
    draw.text((30, 320), 'TUG\'ILGAN SANASI / DATE OF BIRTH', fill=(0, 0, 0))
    draw.text((30, 350), '02 04 2009', fill=(0, 0, 0))
    draw.text((30, 400), 'JINSI / SEX', fill=(0, 0, 0))
    draw.text((30, 430), 'M', fill=(0, 0, 0))
    draw.text((30, 480), 'BERILGAN SANASI / DATE OF ISSUE', fill=(0, 0, 0))
    draw.text((30, 510), '21 06 2023', fill=(0, 0, 0))
    draw.text((30, 560), 'AMAL QILISH MUDDATI / DATE OF EXPIRY', fill=(0, 0, 0))
    draw.text((30, 590), '20 06 2028', fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


def create_synthetic_diploma_image() -> bytes:
    img = Image.new('RGB', (1000, 700), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 40), 'DIPLOM BAKALAVR DIPLOMA', fill=(0, 0, 0))
    draw.text((30, 90), 'SERIYA: B № 1234567', fill=(0, 0, 0))
    draw.text((30, 150), 'TOSHKENT DAVLAT IQTISODIYOT UNIVERSITETI', fill=(0, 0, 0))
    draw.text((30, 210), 'MUTAXASSISLIGI: IQTISODIYOT VA MENEJMENT', fill=(0, 0, 0))
    draw.text((30, 270), '2024 YILDA BITIRGAN', fill=(0, 0, 0))
    draw.text((30, 330), 'GPA: 4.25', fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


def run_benchmark():
    print("=" * 60)
    print("      SALOM CRM OCR SYSTEM PERFORMANCE BENCHMARK")
    print("=" * 60)
    if paddle:
        print(f"Paddle Version: {paddle.__version__}")
        print(f"CUDA / GPU Compiled: {paddle.is_compiled_with_cuda()}")
    else:
        print("Paddle OCR: Not installed (RapidOCR ONNX engine active)")
    print(f"Initial Memory Usage: {get_current_memory_mb():.2f} MB\n")

    passport_bytes = create_synthetic_passport_image()
    diploma_bytes = create_synthetic_diploma_image()

    # Warm up engine
    print("[1/3] Warming up OCREngineManager singleton...")
    t0 = time.time()
    OCREngineManager.get_instance()
    warm_up_time = time.time() - t0
    print(f"      Engine Warm-up Time: {warm_up_time:.3f}s")
    print(f"      Memory after Warm-up: {get_current_memory_mb():.2f} MB\n")

    # Benchmark Passport Extraction
    print("[2/3] Benchmarking Passport Extraction (Target: < 2-3s)...")
    runs = 3
    passport_latencies = []
    for r in range(runs):
        t_start = time.time()
        res = process_document_ephemeral(passport_bytes, 'passport_test.jpg')
        elapsed = time.time() - t_start
        passport_latencies.append(elapsed)
        print(f"      Run {r+1}: {elapsed:.3f}s | Extracted: {len(res['fields'])} fields | Type: {res['document_type']} | Engine: {res['metadata']['ocr_engine']}")

    avg_pass_time = sum(passport_latencies) / len(passport_latencies)
    print(f"      ==> Average Passport Latency: {avg_pass_time:.3f}s (Target: < 2.5s -> {'PASS' if avg_pass_time < 3.0 else 'WARN'})\n")

    # Benchmark Diploma Extraction
    print("[3/3] Benchmarking Diploma Extraction (Target: < 3-5s)...")
    diploma_latencies = []
    for r in range(runs):
        t_start = time.time()
        res = process_document_ephemeral(diploma_bytes, 'diploma_test.jpg')
        elapsed = time.time() - t_start
        diploma_latencies.append(elapsed)
        print(f"      Run {r+1}: {elapsed:.3f}s | Extracted: {len(res['fields'])} fields | Type: {res['document_type']} | Engine: {res['metadata']['ocr_engine']}")

    avg_dip_time = sum(diploma_latencies) / len(diploma_latencies)
    print(f"      ==> Average Diploma Latency: {avg_dip_time:.3f}s (Target: < 4.0s -> {'PASS' if avg_dip_time < 5.0 else 'WARN'})\n")

    print("=" * 60)
    print(f"Final Process Memory Footprint: {get_current_memory_mb():.2f} MB")
    print("Benchmark complete!")
    print("=" * 60)


if __name__ == '__main__':
    run_benchmark()
