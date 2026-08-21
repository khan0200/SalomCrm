import os
import sys
import threading
from django.apps import AppConfig


class StudentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.students'

    def ready(self):
        # Pre-warm OCR engine in a background thread only during runserver/gunicorn
        if 'runserver' in sys.argv or os.environ.get('RUN_MAIN') == 'true':
            def warm_up():
                try:
                    from .ocr_service import OCREngineManager
                    OCREngineManager.get_instance()
                except Exception:
                    pass

            t = threading.Thread(target=warm_up, daemon=True)
            t.start()
