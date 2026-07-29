from django.shortcuts import render, redirect
from django.views.generic import CreateView, TemplateView, View
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from .models import *
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import *
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core import signing
from django.core.mail import send_mail
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
# Create your views here.

# メールアドレス変更用トークンの設定
# salt: 他の用途の署名付きトークンと使い回されないようにするための識別子
# max_age: 確認URLの有効期限（秒）。24時間で切れる
EMAIL_CHANGE_SALT = 'dayline.email_change'
EMAIL_CHANGE_TOKEN_MAX_AGE = 60 * 60 * 24

# ログイン
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import SetPasswordForm


class LoginView(LoginView):
    template_name = 'login.html'
    next_page = reverse_lazy('DayLine_1_DayLine:index')
    redirect_authenticated_user = True

    def form_valid(self, form):
        remember = self.request.POST.get('remember')
        response = super().form_valid(form)
        if remember:
            self.request.session.set_expiry(timedelta(days=30))
        else:
            self.request.session.set_expiry(0)
        return response


# サインアップ
class SignupView(CreateView):
    template_name = 'signup.html'

    # 使用するフォーム
    form_class = CustomUserCreationForm
    # サインアップ(新規登録)が成功した場合に移動するページ
    success_url = reverse_lazy('DayLine_1_DayLine:index')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse_lazy('DayLine_1_DayLine:index'))
        return super().dispatch(request, *args, **kwargs)

    # モデル(データベース)に保存する処理など
    def form_valid(self, form):
        user = form.save()
        self.object = user
        return super().form_valid(form)


#アカウントの設定
# LoginRequiredMixin: get_object() が request.user を返すため、未ログインだと
# AnonymousUser が渡されて予期しない動作になる。必ずログインを required にする
class Account_setting(LoginRequiredMixin, UpdateView):
    template_name = "profile_setting.html"
    model = CustomUser
    success_url = reverse_lazy('DayLine_3_accounts:settings')
    form_class = AccountSettingForm

    # このメソッドをオーバーライドすることでurlにpkを載せてページに飛ばなくてもよくなる
    def get_object(self, queryset=None):

        return self.request.user  # URLのpk不要、ログインユーザーを直接返す
    def get_success_url(self):
        return reverse_lazy('DayLine_3_accounts:settings')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["name"] = self.request.user.username
        return context


# --------------------- セキュリティ設定（パスワード変更・メールアドレス変更） ---------------------

SECURITY_TEMPLATE = 'security_setting.html'


def build_security_context(user, password_form=None, email_form=None):
    """
    セキュリティ設定画面に渡すcontextを組み立てる。

    表示用のGETと、バリデーションエラー時の再描画で同じ内容を使いたいので関数に切り出す。
    エラーになったフォームを引数で渡すと、入力値とエラーを保持したまま再表示できる。
    """
    return {
        'name': user.username,
        'password_form': password_form or AccountPasswordChangeForm(user=user),
        'email_form': email_form or EmailChangeForm(user=user),
        # Googleログインのみのアカウントはパスワードを持っていないので画面上でも区別する
        'has_password': user.has_usable_password(),
    }


class SecuritySetting(LoginRequiredMixin, TemplateView):
    """
    パスワード変更とメールアドレス変更を1画面にまとめた設定ページ。
    実際の更新処理はそれぞれ PasswordChange / EmailChangeRequest が受け持つ。
    """
    template_name = SECURITY_TEMPLATE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_security_context(self.request.user))
        return context


class PasswordChange(LoginRequiredMixin, View):
    """パスワード変更の送信先。成功したらセッションを維持したままリダイレクトする。"""

    def post(self, request, *args, **kwargs):
        form = AccountPasswordChangeForm(user=request.user, data=request.POST)
        if not form.is_valid():
            # エラーを保持したまま設定画面を再描画する
            # ※ SecuritySetting は TemplateView（GET専用）なのでPOSTのまま渡すと405になる。
            #    テンプレートを直接renderする
            return render(request, SECURITY_TEMPLATE,
                          build_security_context(request.user, password_form=form))

        form.save()
        # パスワードを変えるとセッションのハッシュが変わってログアウトしてしまうので、
        # 現在のセッションだけ張り直す
        update_session_auth_hash(request, form.user)
        messages.success(request, 'パスワードを変更しました。')
        return redirect('DayLine_3_accounts:security')

    def get(self, request, *args, **kwargs):
        # 直接GETされたら設定画面に戻す
        return redirect('DayLine_3_accounts:security')


class EmailChangeRequest(LoginRequiredMixin, View):
    """
    メールアドレス変更の申請を受け付けて、新しいアドレス宛に確認メールを送る。

    この時点ではDBのメールアドレスは変更しない。
    署名付きトークン（django.core.signing）に「誰が・どのアドレスに変えたいか」を入れて
    URLに載せ、新アドレスでリンクを踏めたときだけ確定させる。
    トークン自体に情報を持たせるので、申請用のテーブルは不要。
    """

    def post(self, request, *args, **kwargs):
        form = EmailChangeForm(user=request.user, data=request.POST)
        if not form.is_valid():
            # エラーを保持したまま設定画面を再描画する（TemplateViewはGET専用なので直接render）
            return render(request, SECURITY_TEMPLATE,
                          build_security_context(request.user, email_form=form))

        new_email = form.cleaned_data['new_email']

        # 改ざんできない署名付きトークンを作る（有効期限は確認時にチェックする）
        token = signing.dumps(
            {'user_id': str(request.user.pk), 'new_email': new_email},
            salt=EMAIL_CHANGE_SALT,
        )
        confirm_url = request.build_absolute_uri(
            reverse_lazy('DayLine_3_accounts:email_change_confirm', kwargs={'token': token})
        )

        subject = 'メールアドレス変更の確認 | DayLine'
        message = (
            f'{request.user.username} さん\n\n'
            'DayLineのメールアドレス変更を受け付けました。\n'
            '以下のURLを開くと変更が完了します。\n\n'
            f'{confirm_url}\n\n'
            f'このURLの有効期限は{EMAIL_CHANGE_TOKEN_MAX_AGE // 3600}時間です。\n'
            '心当たりがない場合は、このメールを破棄してください。\n'
        )
        # 確認メールは「新しいアドレス」宛に送る（そのアドレスの持ち主であることの確認）
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_email])

        messages.success(
            request,
            f'{new_email} 宛に確認メールを送信しました。メール内のURLを開くと変更が完了します。'
        )
        return redirect('DayLine_3_accounts:security')

    def get(self, request, *args, **kwargs):
        return redirect('DayLine_3_accounts:security')


class EmailChangeConfirm(LoginRequiredMixin, View):
    """確認メールのURLを開いたときにメールアドレスを確定させるビュー。"""

    def get(self, request, token, *args, **kwargs):
        try:
            data = signing.loads(
                token,
                salt=EMAIL_CHANGE_SALT,
                max_age=EMAIL_CHANGE_TOKEN_MAX_AGE,
            )
        except signing.SignatureExpired:
            messages.error(request, '確認URLの有効期限が切れています。もう一度お試しください。')
            return redirect('DayLine_3_accounts:security')
        except signing.BadSignature:
            messages.error(request, '確認URLが不正です。')
            return redirect('DayLine_3_accounts:security')

        # トークンを発行した本人がログインしているかを確認する
        # （URLを他人に踏ませて別アカウントのアドレスを書き換えられないようにする）
        if str(request.user.pk) != data.get('user_id'):
            messages.error(request, '確認URLの発行者と異なるアカウントでログインしています。')
            return redirect('DayLine_3_accounts:security')

        new_email = data.get('new_email')
        # 申請してから確認するまでの間に他の人が同じアドレスを登録している可能性があるので再確認する
        if CustomUser.objects.filter(email__iexact=new_email).exclude(pk=request.user.pk).exists():
            messages.error(request, 'このメールアドレスは既に使われています。')
            return redirect('DayLine_3_accounts:security')

        request.user.email = new_email
        request.user.save(update_fields=['email'])
        messages.success(request, f'メールアドレスを {new_email} に変更しました。')
        return redirect('DayLine_3_accounts:security')



# ログアウト状態でアクセスして情報を取得されないようにLoginRequiredMixinを付ける
class Profile_Api(LoginRequiredMixin,View):
    
    def get(self, request, *args, **kwargs):
        info = request.user
        data = [{
            "pk":info.id,
            "username":info.username,
            "email":info.email
        }]
        return JsonResponse(data, safe=False)


#パスワードリセット系(参考:https://qiita.com/haruki-lo-shelon/items/068addcb6c8f3019d345)

class CustomSetPasswordForm(SetPasswordForm):
    """
    パスワードを忘れた人がメールのリンクから新しいパスワードを設定する画面のフォーム。
    サインアップ・パスワード変更と同じ条件をここでも通す。
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget = forms.PasswordInput(attrs={
            'placeholder': '新しいパスワード',
            'id': 'id_new_password1',   # other.js が入力チェックの表示に使うid
        })
        self.fields['new_password2'].widget = forms.PasswordInput(attrs={
            'placeholder': '新しいパスワード（確認用）',
            'id': 'id_new_password2',
        })

    def clean_new_password1(self):
        # リセット経由でも同じパスワード条件を必ず検証する
        # （ここを通さないと、リセット画面からなら条件を満たさないパスワードを設定できてしまう）
        return validate_password_rule(self.cleaned_data.get('new_password1'))


class PassForget(PasswordResetView):
    """パスワード変更用URLの送付ページ"""
    subject_template_name = 'mail/subject.txt'
    email_template_name = 'mail/message.txt'
    template_name = 'pass_forget.html'
    success_url = reverse_lazy('DayLine_3_accounts:password_reset_done')

#テンプレート未作成
class PasswordResetDone(PasswordResetDoneView):
    """パスワード変更用URLを送りましたページ"""
    template_name = 'password_reset_done.html'

class PassReset(PasswordResetConfirmView):
    """新パスワード入力ページ"""
    # 指定しないとDjango標準のSetPasswordFormが使われ、DayLineのパスワード条件が効かない
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('DayLine_3_accounts:success')
    template_name = 'password_reset.html'

class PassResetSuc(PasswordResetCompleteView):
    """新パスワード設定しましたページ"""
    template_name = 'password_reset_success.html'
