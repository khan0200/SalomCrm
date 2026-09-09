from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.test import SimpleTestCase
from apps.core.telegram_service import (
    resolve_student_id,
    notify_payment_received,
    notify_discount_added,
    notify_withdrawal,
    notify_payment_deleted
)

class TelegramServiceStudentIdTestCase(SimpleTestCase):
    def test_resolve_student_id_from_student_obj(self):
        student = MagicMock()
        student.id = "G45"
        student.payment_id = "PG45"

        payment = MagicMock()
        payment.student_id = "PG45"
        payment.student = student

        self.assertEqual(resolve_student_id(payment, student), "G45")
        self.assertEqual(resolve_student_id(payment, None), "G45")
        self.assertEqual(resolve_student_id(None, student), "G45")

    def test_resolve_student_id_from_payment_id_fallback(self):
        payment = MagicMock()
        payment.student_id = "PG45"
        payment.student = None

        # Should strip leading 'P' if student not in DB/mock
        self.assertEqual(resolve_student_id(payment, None), "G45")

    def test_resolve_student_id_from_dict(self):
        payment_dict = {"student_id": "PG45"}
        self.assertEqual(resolve_student_id(payment_dict, None), "G45")

    def test_resolve_student_id_empty(self):
        self.assertEqual(resolve_student_id(None, None), "-")

    @patch("apps.core.telegram_service.send_telegram_notification")
    def test_notify_payment_received_uses_student_id(self, mock_send):
        student = MagicMock()
        student.id = "G45"
        student.full_name = "KHAYRULLAYEV SARDOR ORIFJON UGLI"
        student.tariff = "REGIONAL VISA"
        student.balance = Decimal("-22000000")
        student.tenant = None

        payment = MagicMock()
        payment.student_id = "PG45"
        payment.student_name = "KHAYRULLAYEV SARDOR ORIFJON UGLI"
        payment.amount = Decimal("2000000")
        payment.method = "Karta Abdulaziz"
        payment.received_by = "ABDULAZIZ"
        payment.notes = "SHARTNOMA UCHUN"
        payment.student = student
        payment.tenant = None

        notify_payment_received(payment, student)

        mock_send.assert_called_once()
        msg = mock_send.call_args[0][0]
        self.assertIn("🆔 <b>ID:</b> G45", msg)
        self.assertNotIn("🆔 <b>ID:</b> PG45", msg)
        self.assertIn("👤 <b>Name:</b> KHAYRULLAYEV SARDOR ORIFJON UGLI", msg)
        self.assertIn("📰 <b>Tariff:</b> REGIONAL VISA", msg)
        self.assertIn("💰 <b>Amount:</b> 2 000 000 UZS", msg)
        self.assertIn("💼 <b>Balance:</b> -22 000 000 UZS", msg)

    @patch("apps.core.telegram_service.send_telegram_notification")
    def test_notify_discount_added_uses_student_id(self, mock_send):
        student = MagicMock()
        student.id = "G45"
        student.full_name = "KHAYRULLAYEV SARDOR ORIFJON UGLI"
        student.balance = Decimal("-20000000")
        student.tenant = None

        payment = MagicMock()
        payment.student_id = "PG45"
        payment.amount = Decimal("2000000")
        payment.notes = "DISCOUNT"
        payment.student = student
        payment.tenant = None

        notify_discount_added(payment, student)

        mock_send.assert_called_once()
        msg = mock_send.call_args[0][0]
        self.assertIn("🆔 <b>ID:</b> G45", msg)
        self.assertNotIn("🆔 <b>ID:</b> PG45", msg)

    @patch("apps.core.telegram_service.send_telegram_notification")
    def test_notify_withdrawal_uses_student_id(self, mock_send):
        student = MagicMock()
        student.id = "G45"
        student.full_name = "KHAYRULLAYEV SARDOR ORIFJON UGLI"
        student.balance = Decimal("-24000000")
        student.tenant = None

        payment = MagicMock()
        payment.student_id = "PG45"
        payment.amount = Decimal("2000000")
        payment.notes = "WITHDRAWAL"
        payment.student = student
        payment.tenant = None

        notify_withdrawal(payment, student)

        mock_send.assert_called_once()
        msg = mock_send.call_args[0][0]
        self.assertIn("🆔 <b>Student ID:</b> G45", msg)
        self.assertNotIn("🆔 <b>Student ID:</b> PG45", msg)

    @patch("apps.core.telegram_service.send_telegram_notification")
    def test_notify_payment_deleted_uses_student_id(self, mock_send):
        student = MagicMock()
        student.id = "G45"
        student.full_name = "KHAYRULLAYEV SARDOR ORIFJON UGLI"
        student.balance = Decimal("-24000000")
        student.tenant = None

        payment = MagicMock()
        payment.student_id = "PG45"
        payment.amount = Decimal("2000000")
        payment.student = student
        payment.tenant = None

        notify_payment_deleted(payment, student)

        mock_send.assert_called_once()
        msg = mock_send.call_args[0][0]
        self.assertIn("🆔 <b>ID:</b> G45", msg)
        self.assertNotIn("🆔 <b>ID:</b> PG45", msg)
