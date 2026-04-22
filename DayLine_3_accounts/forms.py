from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


# サインアップ
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email", "username", "password1", "password2")


    email = forms.EmailField(
        widget = forms.TextInput(
            attrs={
                'placeholder': 'example@email.com',
                'class':'signup-form-input',
                })
    )
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'ユーザー名を入力',
                'class':'signup-form-input',
                }), 
        max_length=20, 
        required=False
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "パスワード",
                "id": "password-1",
                "class": "signup-form-input",
            }
        )
    )


    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "パスワード(確認用)",
                "id": "password-2",
                "class": "signup-form-input",
            }
        )
    )


# アカウント設定
class AccountSettingForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ("username", "birthday", "word", "icon")

        widgets = {
            "birthday": forms.DateInput(attrs={
                "type": "text",
                "class": "date-picker",
                "placeholder":"任意"
            }),
            "username": forms.TextInput(attrs={
                "placeholder": "ユーザー名を入力"
            }),
            "word": forms.Textarea(attrs={
                "placeholder": "一言",
                "rows": 3
            }),
            'icon': forms.FileInput(attrs={
                'style': 'display: none;'  # 隠す
            })
        }
    