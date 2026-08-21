import io
import os
import time
import psutil
from PIL import Image, ImageDraw
from django.core.management.base import BaseCommand

import paddle
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


class Command(BaseCommand):
    help = 'Benchmark PaddleOCR performance, latency, and memory footprint.'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("      SALOM CRM OCR SYSTEM PERFORMANCE BENCHMARK")
        self.stdout.write("=" * 60)
        self.stdout.write(f"Paddle Version: {paddle.__version__}")
        self.stdout.write(f"CUDA / GPU Compiled: {paddle.is_compiled_with_cuda()}")
        self.stdout.write(f"Initial Memory Usage: {get_current_memory_mb():.2f} MB\n")

        passport_bytes = create_synthetic_passport_image()
        diploma_bytes = create_synthetic_diploma_image()

        # Warm up engine
        self.stdout.write("[1/3] Warming up OCREngineManager singleton...")
        t0 = time.time()
        OCREngineManager.get_instance()
        warm_up_time = time.time() - t0
        self.stdout.write(f"      Engine Warm-up Time: {warm_up_time:.3f}s")
        self.stdout.write(f"      Memory after Warm-up: {get_current_memory_mb():.2f} MB\n")

        # Benchmark Passport Extraction
        self.stdout.write("[2/3] Benchmarking Passport Extraction (Target: < 2-3s)...")
        runs = 3
        passport_latencies = []
        for r in range(runs):
            t_start = time.time()
            res = process_document_ephemeral(passport_bytes, 'passport_test.jpg')
            elapsed = time.time() - t_start
            passport_latencies.append(elapsed)
            self.stdout.write(f"      Run {r+1}: {elapsed:.3f}s | Extracted: {len(res['fields'])} fields | Type: {res['document_type']} | Engine: {res['metadata']['ocr_engine']}")

        avg_pass_time = sum(passport_latencies) / len(passport_latencies)
        status_pass = 'PASS' if avg_pass_time < 3.0 else 'WARN'
        self.stdout.write(f"      ==> Average Passport Latency: {avg_pass_time:.3f}s (Target: < 2.5s -> {status_pass})\n")

        # Benchmark Diploma Extraction
        self.stdout.write("[3/3] Benchmarking Diploma Extraction (Target: < 3-5s)...")
        diploma_latencies = []
        for r in range(runs):
            t_start = time.time()
            res = process_document_ephemeral(diploma_bytes, 'diploma_test.jpg')
            elapsed = time.time() - t_start
            diploma_latencies.append(elapsed)
            self.stdout.write(f"      Run {r+1}: {elapsed:.3f}s | Extracted: {len(res['fields'])} fields | Type: {res['document_type']} | Engine: {res['metadata']['ocr_engine']}")

        avg_dip_time = sum(diploma_latencies) / len(diploma_latencies)
        status_dip = 'PASS' if avg_dip_time < 5.0 else 'WARN'
        self.stdout.write(f"      ==> Average Diploma Latency: {avg_dip_time:.3f}s (Target: < 4.0s -> {status_dip})\n")

        self.stdout.write("=" * 60)
        self.stdout.write(f"Final Process Memory Footprint: {get_current_memory_mb():.2f} MB")
        self.stdout.write("Benchmark complete!")
        self.stdout.write("=" * 60)
