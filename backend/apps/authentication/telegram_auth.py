import hmac
import hashlib
import time
from typing import Dict, Any, Tuple
from django.conf import settings


def verify_telegram_authorization(auth_data: Dict[str, Any], max_age_seconds: int = 86400) -> Tuple[bool, str]:
    """
    Verifies Telegram Login Widget cryptographic authorization hash according to
    https://core.telegram.org/widgets/login#checking-authorization

    :param auth_data: Dictionary containing fields received from Telegram:
                      'id', 'first_name', 'last_name', 'username', 'photo_url', 'auth_date', 'hash'
    :param max_age_seconds: Max allowable age of auth_date (defaults to 24 hours / 86400s)
    :return: (is_valid: bool, error_message: str)
    """
    received_hash = auth_data.get('hash')
    if not received_hash:
        return False, 'Missing verification hash.'

    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not bot_token:
        return False, 'TELEGRAM_BOT_TOKEN is not configured on the server.'

    # Step 1: Check auth_date is within allowed window
    auth_date = auth_data.get('auth_date')
    if not auth_date:
        return False, 'Missing auth_date.'

    try:
        auth_timestamp = int(auth_date)
        current_timestamp = int(time.time())
        if current_timestamp - auth_timestamp > max_age_seconds:
            return False, 'Authorization data is expired. Please try logging in again.'
    except (ValueError, TypeError):
        return False, 'Invalid auth_date format.'

    # Step 2: Construct data-check-string (all keys except 'hash', sorted alphabetically)
    check_pairs = []
    for k in sorted(auth_data.keys()):
        if k != 'hash' and auth_data[k] is not None:
            check_pairs.append(f"{k}={auth_data[k]}")

    data_check_string = '\n'.join(check_pairs)

    # Step 3: Compute secret_key = SHA256(bot_token)
    secret_key = hashlib.sha256(bot_token.encode('utf-8')).digest()

    # Step 4: Compute HMAC-SHA256(secret_key, data_check_string)
    computed_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()

    # Step 5: Constant-time string comparison to prevent timing attacks
    if not hmac.compare_digest(computed_hash, received_hash):
        return False, 'Telegram authorization signature mismatch / invalid hash.'

    return True, ''
