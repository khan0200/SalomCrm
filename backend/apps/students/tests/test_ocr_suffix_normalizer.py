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
            # KIZI is a valid passport spelling, not an OCR error: it must be
            # preserved as-is rather than rewritten to QIZI.
            ("KIZI", "KIZI"),
            ("KIZL", "KIZI"),
            ("KYZY", "KIZI"),
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

    def test_real_names_are_never_over_corrected(self):
        """
        Regression guard: real given names that merely resemble a patronymic
        suffix must be preserved verbatim. Previously ODIL -> UGLI (via the
        'OGIL' variant), OZODA -> ZODA, EVA -> EVNA, KIZI -> QIZI.
        """
        preserved = [
            "ODIL", "OZODA", "OZOD", "KIZIL", "ZOD", "EVA", "OVA", "ONA",
            "OBID", "OSIM", "ORIF", "OLIM", "ZUHRA", "ZEBO", "OTABEK", "QOSIM",
        ]
        for token in preserved:
            res, changed = normalize_standalone_suffix(token)
            self.assertEqual(res, token, f"Real name '{token}' was over-corrected to '{res}'")
            self.assertFalse(changed, f"Real name '{token}' should not be marked as changed")

    def test_real_names_preserved_in_full_name_context(self):
        cases = [
            "KARIMOV AZIZ ODIL",
            "KARIMOVA OZODA",
            "ISROILOVA UMIDA UCHKUN KIZI",
        ]
        for name in cases:
            self.assertEqual(normalize_full_name(name), name)

    def test_genuine_ocr_errors_still_corrected(self):
        """The conservative gate must not disable real OCR correction."""
        cases = [
            ("QIZ1", "QIZI"), ("QIZl", "QIZI"),
            ("UGLT", "UGLI"), ("UGL1", "UGLI"),
            ("OGIL", "UGLI"), ("OGLI", "UGLI"),
            ("KIZL", "KIZI"),
            ("0VICH", "OVICH"), ("EV1CH", "EVICH"), ("Z0DA", "ZODA"),
        ]
        for inp, expected in cases:
            res, _ = normalize_standalone_suffix(inp)
            self.assertEqual(res, expected, f"OCR error '{inp}' should correct to '{expected}'")


if __name__ == "__main__":
    unittest.main()
