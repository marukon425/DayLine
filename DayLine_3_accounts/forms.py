import re

from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm

from .models import CustomUser


# パスワードの条件（半角英数字のみ・英字と数字を最低1文字ずつ含む）
# 以前は static/js/accounts/other.js のJSだけで判定していたため、
# 開発者ツールでボタンのdisabledを外せば条件を満たさないパスワードでも登録できてしまった。
# 同じ条件をサーバー側でも検証する。
PASSWORD_PATTERN = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]+$')
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 20


def validate_password_rule(password):
    """
    DayLine独自のパスワードルールを検証する。
    条件を満たさない場合は ValidationError を投げる。
    （Djangoの AUTH_PASSWORD_VALIDATORS による共通チェックとは別に走る）
    """
    if password is None:
        return password
    if not (PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH):
        raise forms.ValidationError(
            f'パスワードは{PASSWORD_MIN_LENGTH}〜{PASSWORD_MAX_LENGTH}文字で入力してください。'
        )
    if not PASSWORD_PATTERN.match(password):
        raise forms.ValidationError(
            'パスワードは半角英数字のみで、英字と数字をそれぞれ1文字以上含めてください。'
        )
    return password


# サインアップ
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email", "username", "password1", "password2")

    # 利用規約への同意。JSでボタンを制御しているだけだと直接POSTで素通りできるため、
    # フォーム側でも必須項目として持つ
    terms_of_use = forms.BooleanField(
        required=True,
        error_messages={'required': '利用規約への同意が必要です。'},
        widget=forms.CheckboxInput(attrs={
            'id': 'terms_of_use-check',       # other.js がこのidを見て送信ボタンを制御している
            'class': 'signup-form-input',
        }),
    )

    #ユーザー名のunipueをオフにする
    def clean_username(self):
        return self.cleaned_data.get('username')

    def clean_password1(self):
        # サーバー側でもパスワードの条件を検証する
        return validate_password_rule(self.cleaned_data.get('password1'))
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
                'style': 'display: none;',  # 隠す
                'class': 'edit-icon'
            })
        }


# パスワード変更（ログイン中のユーザーが自分で変更する用）
class AccountPasswordChangeForm(PasswordChangeForm):
    """
    Django標準の PasswordChangeForm に DayLine のパスワードルールを足したもの。
    現在のパスワードの照合・新パスワードの一致チェックは親クラスがやってくれる。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'old_password': '現在のパスワード',
            'new_password1': '新しいパスワード',
            'new_password2': '新しいパスワード（確認用）',
        }
        for name, placeholder in placeholders.items():
            self.fields[name].widget.attrs.update({
                'placeholder': placeholder,
                'class': 'setting-input',
            })

    def clean_new_password1(self):
        return validate_password_rule(self.cleaned_data.get('new_password1'))


# メールアドレス変更の申請
class EmailChangeForm(forms.Form):
    """
    新しいメールアドレスを受け取るフォーム。

    ここでは実際にメールアドレスを書き換えず、確認メールを送るだけにする。
    （他人のメールアドレスを勝手に登録して乗っ取りに使われるのを防ぐため、
      新アドレス側でリンクを踏んで初めて確定する）
    """

    new_email = forms.EmailField(
        label='新しいメールアドレス',
        widget=forms.EmailInput(attrs={
            'placeholder': 'example@email.com',
            'class': 'setting-input',
        })
    )
    # 本人確認のため現在のパスワードを要求する
    # （ログイン中の端末を放置した隙にメールアドレスを乗っ取られるのを防ぐ）
    password = forms.CharField(
        label='現在のパスワード',
        widget=forms.PasswordInput(attrs={
            'placeholder': '現在のパスワード',
            'class': 'setting-input',
        })
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_email(self):
        new_email = self.cleaned_data['new_email'].strip()
        if self.user and new_email.lower() == (self.user.email or '').lower():
            raise forms.ValidationError('現在のメールアドレスと同じです。')
        # CustomUser.email は unique なので、他の人が使っていたら先に弾く
        if CustomUser.objects.filter(email__iexact=new_email).exists():
            raise forms.ValidationError('このメールアドレスは既に使われています。')
        return new_email

    def clean_password(self):
        password = self.cleaned_data['password']
        # Googleログインだけで作られたアカウントは使えるパスワードを持っていない
        if self.user and not self.user.has_usable_password():
            raise forms.ValidationError(
                'このアカウントにはパスワードが設定されていません。先にパスワードを設定してください。'
            )
        if self.user and not self.user.check_password(password):
            raise forms.ValidationError('パスワードが正しくありません。')
        return password
