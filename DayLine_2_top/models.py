from django.db import models

# Create your models here.
class TermsOfUse(models.Model):
    class Meta:
        verbose_name = "利用規約"
        verbose_name_plural = "利用規約"
    
    article_number = models.IntegerField(
        verbose_name="条",
        max_length=100
    )

    article_name = models.CharField(
        verbose_name="条文タイトル",
        max_length=1000
    )

    article_description = models.TextField(
        verbose_name="条文",
        max_length=2000
    )