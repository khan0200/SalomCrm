import io
import concurrent.futures
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from PIL import Image, ImageDraw
import pymupdf

from apps.students.ocr_normalizer import (
    normalize_date,
    normalize_passport_number,
    normalize_gender,
    normalize_phone_number,
    normalize_name,
)
from apps.students.ocr_preprocessor import (
    prepare_document_images,
    deskew_image,
    enhance_contrast,
    PreprocessError,
)
from apps.students.ocr_service import process_document_ephemeral
from django.contrib.auth import get_user_model
User = get_user_model()


class OCRPipelineTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test_ocr@salomcrm.com', password='password123', full_name='OCR Tester')

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def create_passport_image(self) -> bytes:
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

    def create_diploma_image(self) -> bytes:
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

    def create_sample_pdf(self, num_pages: int = 2) -> bytes:
        doc = pymupdf.open()
        for i in range(num_pages):
            page = doc.new_page(width=600, height=800)
            page.insert_text((50, 50), f"PAGE {i+1} PASSPORT UZBEKISTAN FA1234567")
            page.insert_text((50, 100), "FAMILIYASI / SURNAME: TESTOV")
            page.insert_text((50, 150), "ISMI / GIVEN NAMES: TESTBEK")
        buf = io.BytesIO()
        doc.save(buf)
        doc.close()
        return buf.getvalue()

    # 1. Normalization Tests
    def test_date_normalization(self):
        self.assertEqual(normalize_date('02 04 2009'), '2009-04-02')
        self.assertEqual(normalize_date('02.04.2009'), '2009-04-02')
        self.assertEqual(normalize_date('2009-04-02'), '2009-04-02')
        self.assertEqual(normalize_date('02042009'), '2009-04-02')
        self.assertEqual(normalize_date('2006 2028'), '2028-06-20')
        self.assertIsNone(normalize_date('not_a_date'))

    def test_passport_and_phone_normalization(self):
        self.assertEqual(normalize_passport_number('FA 7958189'), 'FA7958189')
        self.assertEqual(normalize_passport_number('aa 1234567'), 'AA1234567')
        self.assertEqual(normalize_gender('M'), 'MALE')
        self.assertEqual(normalize_gender('ayol'), 'FEMALE')
        self.assertEqual(normalize_phone_number('+998 90 123 45 67'), '90-123-45-67')
        self.assertEqual(normalize_name('  ALISHEROV  MUKHAMMAD!  '), 'ALISHEROV MUKHAMMAD')

    # 2. Passport Extraction Test
    def test_passport_extraction_success(self):
        img_bytes = self.create_passport_image()
        result = process_document_ephemeral(img_bytes, 'passport.jpg')

        self.assertEqual(result['document_type'], 'PASSPORT')
        fields = result['fields']
        details = result['field_details']

        self.assertEqual(fields.get('PASSPORT_NUMBER'), 'FA7958189')
        self.assertIn('ALISHEROV', fields.get('FULL_NAME', ''))
        self.assertEqual(fields.get('DATE_OF_BIRTH'), '2009-04-02')
        self.assertEqual(fields.get('DATE_OF_ISSUE'), '2023-06-21')
        self.assertEqual(fields.get('DATE_OF_EXPIRATION'), '2028-06-20')
        self.assertEqual(fields.get('SEX'), 'MALE')

        # Check field details contract
        dob_detail = details.get('DATE_OF_BIRTH')
        self.assertIsNotNone(dob_detail)
        self.assertIn('confidence', dob_detail)
        self.assertTrue(dob_detail['confidence'] >= 0.8)
        self.assertTrue(dob_detail['validated'])
        self.assertIn(dob_detail['source'], ('VIZ', 'MRZ'))

    # 3. Diploma Extraction Test
    def test_diploma_extraction_success(self):
        img_bytes = self.create_diploma_image()
        result = process_document_ephemeral(img_bytes, 'diploma.jpg')

        self.assertEqual(result['document_type'], 'DIPLOMA')
        fields = result['fields']

        self.assertIn('TOSHKENT', fields.get('FINAL_SCHOOL_NAME', ''))
        self.assertEqual(fields.get('DATE_OF_GRADUATION'), '2024-07-20')
        self.assertEqual(fields.get('DATE_OF_ENTRY'), '2020-09-02')  # 2024 - 4 years
        self.assertIn('1234567', fields.get('DEGREE_NO', ''))

    # 4. Multi-Page PDF Processing
    def test_pdf_extraction(self):
        pdf_bytes = self.create_sample_pdf(num_pages=2)
        images = prepare_document_images(pdf_bytes, 'test.pdf', max_pages=3)
        self.assertEqual(len(images), 2)

    # 5. Invalid and Corrupted File Handling
    def test_invalid_corrupted_file_error(self):
        corrupted_bytes = b"corrupted random data not an image"
        with self.assertRaises(PreprocessError):
            prepare_document_images(corrupted_bytes, 'bad.jpg')

    # 6. API Endpoint Multipart Upload Test
    def test_api_extract_document_endpoint(self):
        img_bytes = self.create_passport_image()
        uploaded = SimpleUploadedFile('passport.jpg', img_bytes, content_type='image/jpeg')

        response = self.client.post('/api/students/extract-document/', {'file': uploaded}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['document_type'], 'PASSPORT')
        self.assertEqual(data['fields']['PASSPORT_NUMBER'], 'FA7958189')
        self.assertIn('field_details', data)
        self.assertIn('metadata', data)
        self.assertTrue(data['metadata']['latency_ms'] > 0)

    # 7. Concurrency Test
    def test_concurrent_extractions(self):
        img_bytes = self.create_passport_image()

        def make_call():
            return process_document_ephemeral(img_bytes, 'passport.jpg')

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_call) for _ in range(3)]
            results = [f.result() for f in futures]

        self.assertEqual(len(results), 3)
        for r in results:
            self.assertEqual(r['document_type'], 'PASSPORT')
            self.assertEqual(r['fields']['PASSPORT_NUMBER'], 'FA7958189')
