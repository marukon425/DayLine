from datetime import datetime, timedelta
from .models import Event
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
import pytz


def send_event_notifications():
    jst = pytz.timezone('Asia/Tokyo')
    now = timezone.now().astimezone(jst)# いつもだったらdatetimeを使うけど現地時刻が時限通知に影響が出るからtimezoneを使う
    target = now + timedelta(minutes=30)

    # 30分後に始まるイベントだけをを絞り込む
    events = Event.objects.filter(
        start_date=target.date(),
        start_time__hour=target.hour,
        start_time__minute=target.minute,
    )

    for event in events:
        recipient_list = []
        for memmber in event.room.roommember_set.all():
            recipient_list.append(memmber.user.email)
        subject = "30分前"
        message = f"""
        {event.room.room_name} - {event.title}
        開始：{event.start_date}
        """
        from_email = settings.DEFAULT_FROM_EMAIL
        send_mail(subject, message, from_email, recipient_list)

