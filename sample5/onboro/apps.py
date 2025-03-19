from django.apps import AppConfig

class OnboroConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'onboro'

    def ready(self):
        import onboro.signals  # signals.pyをインポート
