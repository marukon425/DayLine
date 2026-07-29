from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

# グーグルアカウント連携したときにパスワードの上書きをキャンセルする
class NoPasswordSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = sociallogin.user
        # 既存ユーザーならパスワードを触らない
        if user.pk:
            existing = user.__class__.objects.get(pk=user.pk)
            sociallogin.user = existing
            return existing
        return super().save_user(request, sociallogin, form)