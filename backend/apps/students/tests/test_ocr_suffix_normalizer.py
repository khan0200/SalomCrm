import unittest
from apps.students.ocr_suffix_normalizer import (
    normalize_full_name,
    normalize_standalone_suffix,
    normalize_attached_suffix,
    normalize_extracted_fields
)


class TestOCRSuffixNormalizer(unittest.TestCase):
    def test_standalone_ugli_variations(self):
        cases = [
            ("UGLI", "UGLI"),
            ("UGLT", "UGLI"),
            ("UGL1", "UGLI"),
            ("UGLl", "UGLI"),
            ("UGL", "UGLI"),
            ("OGLI", "UGLI"),
            ("O'GLI", "UGLI"),
            ("O‘GLI", "UGLI"),
            ("O'G'LI", "UGLI"),
            ("AUGLI", "UGLI"),
            ("AUGL", "UGLI"),
            ("AUGN", "UGLI"),
        ]
        for inp, expected in cases:
            res, _ = normalize_standalone_suffix(inp)
            self.assertEqual(res, expected, f"Failed for standalone token: {inp}")

    def test_standalone_qizi_variations(self):
        cases = [
            ("QIZI", "QIZI"),
            ("QIZl", "QIZI"),
            ("QIZ1", "QIZI"),
            ("QIZT", "QIZI"),
            ("QIZ", "QIZI"),
            ("KIZI", "QIZI"),
            ("KYZY", "QIZI"),
        ]
        for inp, expected in cases:
            res, _ = normalize_standalone_suffix(inp)
            self.assertEqual(res, expected, f"Failed for standalone token: {inp}")

    def test_standalone_ovich_and_zoda(self):
        cases = [
            ("OVICH", "OVICH"),
            ("OVlCH", "OVICH"),
            ("0VICH", "OVICH"),
            ("0VlCH", "OVICH"),
            ("OVNA", "OVNA"),
            ("0VNA", "OVNA"),
            ("ZODA", "ZODA"),
            ("Z0DA", "ZODA"),
            ("ZADA", "ZODA"),
        ]
        for inp, expected in cases:
            res, _ = normalize_standalone_suffix(inp)
            self.assertEqual(res, expected, f"Failed for standalone token: {inp}")

    def test_attached_surname_suffixes(self):
        cases = [
            ("ZOKIR0V", "ZOKIROV"),
            ("KARIM0VA", "KARIMOVA"),
            ("AL1YEV", "ALIYEV"),
            ("TURSUN0V", "TURSUNOV"),
            ("ISMOILOVZ0DA", "ISMOILOVZODA"),
            ("VALIYEV0VICH", "VALIYEVOVICH"),
            ("RUSTAM0VNA", "RUSTAMOVNA"),
        ]
        for inp, expected in cases:
            res, _ = normalize_attached_suffix(inp)
            self.assertEqual(res, expected, f"Failed for attached suffix: {inp}")

    def test_full_name_normalization(self):
        cases = [
            ("ZOKIROV BEKHRUZ BOTIR UGLT", "ZOKIROV BEKHRUZ BOTIR UGLI"),
            ("ZOKIROV BEKHRUZ BOTIR UGL1", "ZOKIROV BEKHRUZ BOTIR UGLI"),
            ("ZOKIROV BEKHRUZ BOTIR UGLl", "ZOKIROV BEKHRUZ BOTIR UGLI"),
            ("ZOKIROV BEKHRUZ BOTIR UGL", "ZOKIROV BEKHRUZ BOTIR UGLI"),
            ("KARIMOVA DILNOZA ANVAR QIZl", "KARIMOVA DILNOZA ANVAR QIZI"),
            ("KARIMOVA DILNOZA ANVAR QIZ1", "KARIMOVA DILNOZA ANVAR QIZI"),
            ("RAHMATZ0DA NODIR BAXTIYOR OVICH", "RAHMATZODA NODIR BAXTIYOR OVICH"),
            ("TURSUN0V JASUR ALIEV0VICH", "TURSUNOV JASUR ALIEVOVICH"),
            ("ALISHER BOTIRUGLT", "ALISHER BOTIR UGLI"),
        ]
        for inp, expected in cases:
            res = normalize_full_name(inp)
            self.assertEqual(res, expected, f"Failed for full name: {inp}")

    def test_false_positives_protection(self):
        # Ordinary words should not be modified
        ordinary_words = [
            "TOSHKENT", "ANDIJON", "SAMARQAND", "GUL", "TOG", "ILHOM", "OLMA", "TUMAN", "SHAHAR"
        ]
        for word in ordinary_words:
            res = normalize_full_name(word)
            self.assertEqual(res, word, f"False positive triggered for word: {word}")

    def test_standard_surname_suffixes_preserved(self):
        standard_cases = [
            ("ISMOILOV", "ISMOILOV"),
            ("ISMOILOVA", "ISMOILOVA"),
            ("ALIEV", "ALIEV"),
            ("ALIEVA", "ALIEVA"),
            ("VALIYEV", "VALIYEV"),
            ("VALIYEVA", "VALIYEVA"),
            ("RAHMATZODA", "RAHMATZODA"),
            ("RAHMATZADA", "RAHMATZADA"),
            ("BAXTIYOROV", "BAXTIYOROV"),
            ("ANVAROVNA", "ANVAROVNA"),
            ("BOTIROVICH", "BOTIROVICH"),
        ]
        for inp, expected in standard_cases:
            res = normalize_full_name(inp)
            self.assertEqual(res, expected, f"Standard suffix modified: {inp}")

    def test_field_aware_dictionary_normalization(self):
        payload = {
            "FULL_NAME": "ZOKIROV BEKHRUZ BOTIR UGLT",
            "FATHER_FULLNAME": "ZOKIROV BOTIR UGL1",
            "MOTHER_FULLNAME": "ZOKIROVA NODIRA ANVAR QIZl",
            "PASSPORT_NUMBER": "FA7452027",
            "FINAL_SCHOOL_NAME": "SECONDARY SCHOOL NO 14",
            "SEX": "MALE",
        }
        normalized = normalize_extracted_fields(payload)
        self.assertEqual(normalized["FULL_NAME"], "ZOKIROV BEKHRUZ BOTIR UGLI")
        self.assertEqual(normalized["FATHER_FULLNAME"], "ZOKIROV BOTIR UGLI")
        self.assertEqual(normalized["MOTHER_FULLNAME"], "ZOKIROVA NODIRA ANVAR QIZI")
        self.assertEqual(normalized["PASSPORT_NUMBER"], "FA7452027")  # non-name untouched
        self.assertEqual(normalized["FINAL_SCHOOL_NAME"], "SECONDARY SCHOOL NO 14")


if __name__ == "__main__":
    unittest.main()
