from django.apps import AppConfig


class Dayline1DaylineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'DayLine_1_DayLine'

    # signalsを使えるようにする
    def ready(self):
        import DayLine_1_DayLine.signals  # signals.py を読み込む
