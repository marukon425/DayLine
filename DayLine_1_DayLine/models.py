from django.db import models
from DayLine_3_accounts.models import *
import datetime
from django.urls import reverse
import uuid
# Create your models here.
import uuid
import cloudinary.models


# ルーム


# カラー
class Color(models.Model):
    class Meta:
        verbose_name = "色管理"
        verbose_name_plural = "色管理"

    color_name = models.CharField(
        verbose_name='名前',
        max_length=20
    )

    color = models.CharField(
        max_length=20,
        verbose_name = '色',
    )

    def __str__(self):
        return self.color_name

    def get_absolute_url(self):
        return reverse("Color_detail", kwargs={"pk": self.pk})

# 繰り返し
class Repeat(models.Model):
    class Meta:
        verbose_name = "繰り返し管理"
        verbose_name_plural = "繰り返し管理"

    repeat_name = models.CharField(
        verbose_name='名前',
        max_length=10
    )

    repeat_code = models.CharField(
        verbose_name='コード',
        max_length=30,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.repeat_name
# ルーム
class Room(models.Model):

    class Meta:
        verbose_name = "カレンダー"
        verbose_name_plural = "カレンダー"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
    )

    room_name = models.CharField(
        verbose_name='ルーム名',
        max_length=50
    )
    
    room_description = models.TextField(
        verbose_name= "説明",
        max_length=500,
        null=True,
        blank=True
    )

    room_img = cloudinary.models.CloudinaryField(
        resource_type='image',
        default='images/defaults/calendar/defalt_calendar_img.png',
        blank=True,
        null=True
    )
    owner = models.ForeignKey(
        CustomUser,
        verbose_name='作成者',
        on_delete=models.CASCADE,
        related_name='owned_rooms',
        null=True
    )

    # 公開ルームか切り替える予定
    is_personal = models.BooleanField(
        verbose_name="個人用ルームか",
        default=False
    )

    # 参加url
    join_url = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        null=True
    )

    def __str__(self):
        return self.room_name

    def get_absolute_url(self):
        return reverse("Room_detail", kwargs={"pk": self.pk})

    # 参加urlを自動生成
    # 作成時には自動生成
    def save(self, *args, **kwargs):
        if not self.join_url:
            self.join_url = uuid.uuid4().hex[:10]
        super().save(*args, **kwargs)





# 権限
class Authority(models.Model):
    class Meta:
        verbose_name = "権限セット"
        verbose_name_plural = "権限セット"

    authority_name = models.CharField(
        verbose_name='権限名',
        max_length=20
    )

    authority_code = models.CharField(
        verbose_name='権限',
        max_length=20
    )

    class Meta:
        verbose_name = "Authority"
        verbose_name_plural = "Authoritys"

    def __str__(self):
        return self.authority_name

    def get_absolute_url(self):
        return reverse("Authority_detail", kwargs={"pk": self.pk})


def get_default_authority():
    authority, _ = Authority.objects.get_or_create(
        authority_code="user",
        defaults={"authority_name": "ユーザー"}
    )
    return authority.pk
# ルームメンバー
class RoomMember(models.Model):
    class Meta:
        verbose_name = "カレンダーメンバー"
        verbose_name_plural = "カレンダーメンバー"
        # 同じユーザーが同じルームに入るのを防ぐ
        unique_together = ('room', 'user')
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
    )

    room = models.ForeignKey(
        Room,
        verbose_name='ルーム名',
        on_delete=models.CASCADE,
        null=True
    )

    user = models.ForeignKey(
        CustomUser,
        verbose_name='ユーザー名',
        on_delete=models.CASCADE,
        null=True
    )

    join_at = models.DateTimeField(auto_now_add=True)

    '''
    ルームの作成者にはsuperuserの権限を与える
    権限の種類の設定ができたらデフォルトの値を設定してon_deleteの設定を変える
    '''
    authority = models.ForeignKey(
        Authority,
        verbose_name='権限',
        on_delete=models.PROTECT,
        default= get_default_authority
    )

    def __str__(self):
        return f"{self.room.room_name} - {self.user.username}" if self.room and self.user else "未設定"

    def get_absolute_url(self):
        return reverse("RoomMember_detail", kwargs={"pk": self.pk})



# イベント
class Event(models.Model):
    class Meta:
        verbose_name = "予定"
        verbose_name_plural = "予定"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
    )
    room = models.ForeignKey(
        Room,
        verbose_name='ルーム',
        on_delete=models.CASCADE,
        related_name='events',
        null=True
    )

    title = models.CharField(
        verbose_name='タイトル',
        max_length=100,
    )

    created_by = models.ForeignKey(
        CustomUser,
        verbose_name='作成者',
        on_delete=models.SET_NULL,
        null=True
    )

    # user = models.ForeignKey(
    #     CustomUser,
    #     verbose_name='作成者',
    #     on_delete=models.SET_NULL,
    #     null=True
    # )

    start_date = models.DateField(
        verbose_name='開始日',
    )

    start_time = models.TimeField(
        verbose_name='開始時間',
        default=datetime.time(0, 0, 0),
        blank=True

    )

    end_date = models.DateField(
        verbose_name='終了日',
        null=True,
        blank=True
    )

    end_time = models.TimeField(
        verbose_name='終了時間',
        default=datetime.time(23, 0, 0),
        null=True,
        blank=True
    )

    allday = models.BooleanField(
        verbose_name='終日設定',
        default=True
    )

    color = models.ForeignKey(
        Color,
        verbose_name="色",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    repeat = models.ForeignKey(
        Repeat,
        verbose_name="繰り返し",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    url = models.URLField(
        verbose_name="URL",
        null=True,
        blank=True
    )

    location = models.CharField(
        verbose_name="場所",
        null=True,
        blank=True,
        max_length=100
    )

    memo = models.TextField(
        verbose_name="メモ",
        null=True,
        blank=True,
        max_length=500
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("Event_detail", kwargs={"pk": self.pk})

