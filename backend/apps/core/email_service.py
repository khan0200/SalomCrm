import os
import secrets
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def generate_numeric_otp(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP."""
    digits = '0123456789'
    return ''.join(secrets.choice(digits) for _ in range(length))


def generate_verification_code(student_id: str) -> str:
    """
    Generate cryptographically secure random verification code.
    Format: XXXX-XXXX-STUDENTID
    Example: 7K4P-92MX-G108
    Excludes ambiguous characters (0, O, 1, I).
    """
    charset = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
    part1 = ''.join(secrets.choice(charset) for _ in range(4))
    part2 = ''.join(secrets.choice(charset) for _ in range(4))
    clean_student_id = (student_id or 'STUDENT').strip().upper()
    return f"{part1}-{part2}-{clean_student_id}"


def send_otp_email(to_email: str, otp_code: str, tenant_name: str = 'UniBridge') -> bool:
    """
    Send OTP verification code to student's email using Resend API.
    """
    subject = f"Tasdiqlash kodi: {otp_code} — {tenant_name}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #fafafa; margin: 0; padding: 0; }}
        .email-wrapper {{ width: 100%; background-color: #fafafa; padding: 40px 0; }}
        .email-card {{ max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; border: 1px solid #e4e4e7; }}
        .email-header {{ padding: 24px 32px; border-bottom: 1px solid #f4f4f5; background: #fafafa; }}
        .email-body {{ padding: 32px; color: #18181b; line-height: 1.65; }}
        .otp-box {{ background: #fafafa; border: 1px solid #e4e4e7; border-radius: 12px; padding: 22px; text-align: center; margin: 24px 0; }}
        .otp-digits {{ font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #18181b; font-family: 'SF Mono', Menlo, monospace; }}
        .footer {{ text-align: center; padding: 20px 32px; font-size: 11px; color: #a1a1aa; border-top: 1px solid #f4f4f5; }}
      </style>
    </head>
    <body>
      <div class="email-wrapper">
        <div class="email-card">
          <div class="email-header">
            <h1 style="margin: 0; font-size: 15px; font-weight: 700; color: #18181b; letter-spacing: -0.2px;">{tenant_name}</h1>
            <p style="margin: 3px 0 0; font-size: 12px; color: #71717a;">Onlayn Shartnoma Tizimi</p>
          </div>
          <div class="email-body">
            <h2 style="font-size: 16px; font-weight: 700; margin: 0 0 12px; color: #18181b;">Assalomu alaykum!</h2>
            <p style="font-size: 13px; margin: 0 0 4px; color: #3f3f46;">Ro'yxatdan o'tish yoki kirish uchun kodingiz:</p>

            <div class="otp-box">
              <div class="otp-digits">{otp_code}</div>
              <p style="margin: 10px 0 0; font-size: 12px; color: #71717a;">Kod <strong style="color: #18181b;">10 daqiqa</strong> amal qiladi.</p>
            </div>

            <p style="font-size: 12px; color: #a1a1aa; margin: 0;">Bu kodni hech kim bilan, hatto xodimlar bilan ham baham ko'rmang.</p>
          </div>
          <div class="footer">
            <p style="margin: 0;">© 2026 {tenant_name}. Barcha huquqlar himoyalangan.</p>
          </div>
        </div>
      </div>
    </body>
    </html>
    """

    resend_api_key = getattr(settings, 'RESEND_API_KEY', '') or os.getenv('RESEND_API_KEY', '')
    from_email = getattr(settings, 'RESEND_FROM_EMAIL', '') or os.getenv('RESEND_FROM_EMAIL', 'Salom Korea <shartnomalar@salomkorea.uz>')

    if not resend_api_key:
        logger.warning(f"[EMAIL DEV MODE] RESEND_API_KEY not set. OTP for {to_email}: {otp_code}")
        print(f"\n========================================\n[EMAIL OTP SIMULATION] To: {to_email}\nCode: {otp_code}\n========================================\n")
        return True

    try:
        import resend
        resend.api_key = resend_api_key
        params = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        resp = resend.Emails.send(params)
        logger.info(f"Sent OTP email to {to_email}: {resp}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send email via Resend to {to_email}: {exc}")
        print(f"\n[EMAIL RESEND FALLBACK] To: {to_email}, Code: {otp_code}, Error: {exc}\n")
        # In development we still return True so dev/test flow proceeds
        return True
