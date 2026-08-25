import os
import re
import html
import logging
import threading
from datetime import datetime
from decimal import Decimal
from typing import Optional, Union, List, Any
import requests

logger = logging.getLogger(__name__)

DEFAULT_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
DEFAULT_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def escape_html(text: Any) -> str:
    """Escape HTML characters to prevent breaking Telegram parse_mode='HTML'."""
    if text is None:
        return ""
    return html.escape(str(text).strip())

def format_uzs(amount: Any) -> str:
    """Format decimal/int currency to 1 000 000 format (magnitude only, no sign)."""
    try:
        val = abs(int(Decimal(str(amount))))
        return f"{val:,}".replace(",", " ")
    except Exception:
        try:
            val = abs(int(float(amount)))
            return f"{val:,}".replace(",", " ")
        except Exception:
            return str(amount)

def format_uzs_signed(amount: Any) -> str:
    """
    Format a balance to 1 000 000 format, preserving its sign.
    A negative balance is remaining debt and must render as e.g. "-60 000 000",
    not the unsigned amount format_uzs() gives (which is correct for payment
    amounts, but would hide the debt/overpayment distinction for balance).
    """
    try:
        val = int(Decimal(str(amount)))
    except Exception:
        try:
            val = int(float(amount))
        except Exception:
            return str(amount)
    sign = "-" if val < 0 else ""
    return f"{sign}{abs(val):,}".replace(",", " ")

def _send_telegram_worker(bot_token: str, chat_ids: List[str], message: str) -> None:
    """Worker executed in background thread."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    for cid in chat_ids:
        try:
            payload = {
                "chat_id": cid,
                "text": message,
                "parse_mode": "HTML"
            }
            resp = requests.post(url, json=payload, timeout=6)
            if not resp.ok:
                logger.warning(f"Telegram notification to {cid} failed ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.error(f"Error sending Telegram notification to {cid}: {e}")

def send_telegram_notification(message: str, chat_ids: Optional[Union[str, List[str]]] = None, sync: bool = False) -> bool:
    """
    Sends an HTML formatted message to configured Telegram chats.
    By default runs asynchronously to never block API responses.
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN") or DEFAULT_BOT_TOKEN
    raw_chat_ids = chat_ids or os.environ.get("TELEGRAM_CHAT_ID") or DEFAULT_CHAT_ID

    if not bot_token or not raw_chat_ids:
        logger.info("Telegram notification skipped: bot token or chat ID not set.")
        return False

    if isinstance(raw_chat_ids, str):
        target_ids = [c.strip() for c in raw_chat_ids.split(",") if c.strip()]
    else:
        target_ids = [str(c).strip() for c in raw_chat_ids if str(c).strip()]

    if not target_ids:
        return False

    if sync:
        _send_telegram_worker(bot_token, target_ids, message)
    else:
        t = threading.Thread(target=_send_telegram_worker, args=(bot_token, target_ids, message), daemon=True)
        t.start()

    return True

# ── 1. New Registration Notification ──────────────────────────────────────────
def notify_new_registration(student: Any) -> None:
    try:
        safe_name = escape_html(student.full_name or "Unknown")
        safe_id = escape_html(student.id or "-")
        safe_office = escape_html(student.office or "-")
        
        cur_datetime = datetime.now().strftime("%d/%m/%Y, %H:%M")

        lines = [
            "🆕 <b>New Registration!</b>\n",
            f"👤 <b>Name:</b> {safe_name}",
            f"🆔 <b>ID:</b> {safe_id}",
            f"🏢 <b>Office:</b> {safe_office}",
        ]

        if getattr(student, 'tariff', None):
            lines.append(f"💳 <b>Tariff:</b> {escape_html(student.tariff)}")
        if getattr(student, 'level', None):
            lines.append(f"🎓 <b>Level:</b> {escape_html(student.level)}")
        if getattr(student, 'university1', None):
            lines.append(f"🏛️ <b>University 1:</b> {escape_html(student.university1)}")
        if getattr(student, 'student_group', None):
            lines.append(f"👥 <b>Group:</b> {escape_html(student.student_group)}")
        if getattr(student, 'lead_by', None):
            lines.append(f"🧑💼 <b>Lead By:</b> {escape_html(student.lead_by)}")
        if getattr(student, 'coordinator', None):
            lines.append(f"🛡️ <b>Coordinator:</b> {escape_html(student.coordinator)}")

        lines.append(f"\n📅 <b>Time:</b> {cur_datetime}")
        msg = "\n".join(lines)
        send_telegram_notification(msg)
    except Exception as e:
        logger.error(f"Failed to create new registration telegram message: {e}")

# ── 2. Payment Received Notification ──────────────────────────────────────────
def notify_payment_received(payment: Any, student: Optional[Any] = None) -> None:
    try:
        student_obj = student or getattr(payment, 'student', None)
        safe_id = escape_html(payment.student_id or (student_obj.id if student_obj else "-"))
        safe_name = escape_html(payment.student_name or (student_obj.full_name if student_obj else "Unknown"))

        tariff_name = "-"
        if student_obj and student_obj.tariff:
            tariff_name = student_obj.tariff
            if student_obj.tariff == "E-VISA":
                cert = getattr(student_obj, 'language_certificate', None)
                if cert and cert != "NO CERTIFICATE":
                    tariff_name += " (TIL SERTIFIKATLI)"
                else:
                    tariff_name += " (TIL SERTIFIKATISIZ)"

        amount_str = format_uzs(payment.amount)
        balance_str = format_uzs_signed(student_obj.balance) if student_obj and student_obj.balance is not None else "-"
        method = escape_html(payment.method or "-")
        received_by = escape_html(payment.received_by or "-")
        notes = escape_html(payment.notes or "")
        cur_date = datetime.now().strftime("%d/%m/%Y")

        msg = (
            f"🟩 <b>Payment Received</b>\n\n"
            f"🆔 <b>ID:</b> {safe_id}\n"
            f"👤 <b>Name:</b> {safe_name}\n\n"
            f"📰 <b>Tariff:</b> {escape_html(tariff_name)}\n"
            f"💰 <b>Amount:</b> {amount_str} UZS\n"
            f"💼 <b>Balance:</b> {balance_str} UZS\n"
            f"💳 <b>Payment Type:</b> {method}\n"
            f"🧾 <b>Received by:</b> {received_by}\n\n"
            f"📝 <b>Note:</b> {notes}\n\n"
            f"📅 <b>Date:</b> {cur_date}"
        )
        send_telegram_notification(msg)
    except Exception as e:
        logger.error(f"Failed to create payment received telegram message: {e}")

# ── 3. Discount Added Notification ────────────────────────────────────────────
def notify_discount_added(payment: Any, student: Optional[Any] = None) -> None:
    try:
        student_obj = student or getattr(payment, 'student', None)
        safe_id = escape_html(payment.student_id or (student_obj.id if student_obj else "-"))
        safe_name = escape_html(payment.student_name or (student_obj.full_name if student_obj else "Unknown"))

        amount_str = format_uzs(payment.amount)
        balance_str = format_uzs_signed(student_obj.balance) if student_obj and student_obj.balance is not None else "-"
        notes = escape_html(payment.notes or "")
        cur_date = datetime.now().strftime("%d/%m/%Y")

        msg = (
            f"🟨 <b>Discount Added</b>\n\n"
            f"🆔 <b>ID:</b> {safe_id}\n"
            f"👤 <b>Student:</b> {safe_name}\n"
            f"💰 <b>Amount:</b> {amount_str} UZS\n"
            f"💼 <b>Balance:</b> {balance_str} UZS\n"
            f"📝 <b>Note:</b> {notes}\n\n"
            f"📅 <b>Date:</b> {cur_date}"
        )
        send_telegram_notification(msg)
    except Exception as e:
        logger.error(f"Failed to create discount added telegram message: {e}")

# ── 4. Withdrawal Notification ────────────────────────────────────────────────
def notify_withdrawal(payment: Any, student: Optional[Any] = None) -> None:
    try:
        student_obj = student or getattr(payment, 'student', None)
        safe_id = escape_html(payment.student_id or (student_obj.id if student_obj else "-"))
        safe_name = escape_html(payment.student_name or (student_obj.full_name if student_obj else "General Withdrawal"))

        amount_str = format_uzs(payment.amount)
        balance_str = format_uzs_signed(student_obj.balance) if student_obj and student_obj.balance is not None else "-"
        notes = escape_html(payment.notes or "")
        cur_date = datetime.now().strftime("%d/%m/%Y")

        msg = (
            f"🟥 <b>Withdrawal</b>\n\n"
            f"🆔 <b>Student ID:</b> {safe_id}\n"
            f"👤 <b>Student:</b> {safe_name}\n"
            f"💰 <b>Amount:</b> -{amount_str} UZS\n"
            f"💼 <b>Balance:</b> {balance_str} UZS\n"
            f"📝 <b>Note:</b> {notes}\n\n"
            f"📅 <b>Date:</b> {cur_date}"
        )
        send_telegram_notification(msg)
    except Exception as e:
        logger.error(f"Failed to create withdrawal telegram message: {e}")

# ── 5. Payment Deleted Notification ───────────────────────────────────────────
def notify_payment_deleted(payment: Any, student: Optional[Any] = None) -> None:
    try:
        student_obj = student or getattr(payment, 'student', None)
        safe_id = escape_html(payment.student_id or (student_obj.id if student_obj else "-"))
        safe_name = escape_html(payment.student_name or (student_obj.full_name if student_obj else "Unknown"))

        amount_str = format_uzs(payment.amount)
        balance_str = format_uzs_signed(student_obj.balance) if student_obj and student_obj.balance is not None else "-"

        msg = (
            f"🟥 <b>Payment Deleted</b>\n\n"
            f"🆔 <b>ID:</b> {safe_id}\n"
            f"👤 <b>Student:</b> {safe_name}\n"
            f"💰 <b>Amount:</b> -{amount_str} UZS\n"
            f"💼 <b>Balance:</b> {balance_str} UZS"
        )
        send_telegram_notification(msg)
    except Exception as e:
        logger.error(f"Failed to create payment deleted telegram message: {e}")
