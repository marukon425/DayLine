from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import random
import cloudinary.models


# Create your models here.

# ユーザー情報
class CustomUser(AbstractUser):
    # Userモデルを継承したカスタムユーザーモデル
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ユーザーネームは別に被ってもいい
    username = models.CharField(
        max_length=150,
        unique=False,
    )

    # メールアドレスをログイン用に使うから被るのをなしにする
    email = models.EmailField(
        unique=True,
    )

    word = models.TextField(
        unique=False,
        max_length=500,
        null=True,
        blank=True
    )

    birthday = models.DateField(
        unique=False,
        null=True,
        blank=True
    )

    icon = cloudinary.models.CloudinaryField(
        resource_type='image',
        blank=True,
        null=True
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']