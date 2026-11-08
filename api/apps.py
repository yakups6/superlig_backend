import os
import sys
from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        if 'runserver' in sys.argv and (os.environ.get('RUN_MAIN') == 'true' or '--noreload' in sys.argv):
            try:
                from .integrations import APIFootballService
                APIFootballService.ensure_background_poller()
            except Exception as exc:
                print(f"[ApiConfig] Canlı skor arka plan izleyicisi başlatılamadı: {exc}")
