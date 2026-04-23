from django.shortcuts import render
from django.views.generic import CreateView, TemplateView, View
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from .models import *
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import *
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
# Create your views here.

# ログイン
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import login
class LoginView(LoginView):
    template_name = 'login.html'
    next_page = reverse_lazy('DayLine_1_DayLine:index')


# サインアップ
class SignupView(CreateView):
    template_name = 'signup.html'

    # 使用するフォーム
    form_class = CustomUserCreationForm
    # サインアップ(新規登録)が成功した場合に移動するページ
    success_url = reverse_lazy('DayLine_1_DayLine:index')
    

    # モデル(データベース)に保存する処理など
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        self.object = user
        return super().form_valid(form)


#アカウントの設定
class Account_setting(UpdateView):
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget = forms.PasswordInput(attrs={
            'placeholder': '新しいパスワード'
        })
        self.fields['new_password2'].widget = forms.PasswordInput(attrs={
            'placeholder': '新しいパスワード（確認用）'
        })
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

class PassReset(CustomSetPasswordForm):
    """新パスワード入力ページ"""
    success_url = reverse_lazy('DayLine_3_accounts:success')
    template_name = 'password_reset.html'

class PassResetSuc(PasswordResetCompleteView):
    """新パスワード設定しましたページ"""
    template_name = 'password_reset_success.html'
