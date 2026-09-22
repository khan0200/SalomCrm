import os
import logging
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

logger = logging.getLogger(__name__)

_initialized = False


def _get_firebase_app():
    """Firebase Admin SDK ni bir marta initialize qiladi."""
    global _initialized
    if not _initialized:
        cred_path = os.environ.get(
            'FIREBASE_CREDENTIALS_PATH',
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'firebase-credentials.json')
        )
        if not os.path.exists(cred_path):
            raise FileNotFoundError(
                f"Firebase credentials file not found at: {cred_path}\n"
                "Set FIREBASE_CREDENTIALS_PATH env var or place firebase-credentials.json in backend/ root."
            )
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        _initialized = True
        logger.info("Firebase Admin SDK initialized.")
    return firebase_admin.get_app()


def verify_firebase_phone_token(id_token: str) -> tuple[str, str]:
    """
    Firebase Phone Auth idToken ni tekshirib, (phone_number, uid) qaytaradi.

    Args:
        id_token: Firebase client SDK dan olingan idToken string

    Returns:
        (phone_number, uid) tuple — masalan ("+998901234567", "uid_abc123")

    Raises:
        firebase_admin.auth.InvalidIdTokenError: token noto'g'ri yoki muddati o'tgan
        ValueError: token phone_number claim ini o'z ichiga olmaydi
        FileNotFoundError: credentials fayl topilmadi
    """
    _get_firebase_app()
    decoded = firebase_auth.verify_id_token(id_token)
    phone_number = decoded.get('phone_number')
    uid = decoded.get('uid', '')
    if not phone_number:
        raise ValueError("Firebase token does not contain a phone_number claim. "
                         "Make sure Phone Auth was used (not Email/Password).")
    return phone_number, uid
