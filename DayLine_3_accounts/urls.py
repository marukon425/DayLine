from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'DayLine_3_accounts'
urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('account/settings/', views.Account_setting.as_view(), name='settings'),
    # セキュリティ設定（パスワード変更・メールアドレス変更）
    path('account/security/', views.SecuritySetting.as_view(), name='security'),
    path('account/password/change/', views.PasswordChange.as_view(), name='password_change'),
    path('account/email/change/', views.EmailChangeRequest.as_view(), name='email_change'),
    path('account/email/confirm/<str:token>/', views.EmailChangeConfirm.as_view(), name='email_change_confirm'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('password/forget/', views.PassForget.as_view(), name='passfor'),
    path('password/reset/<uidb64>/<token>/', views.PassReset.as_view(), name='password_reset_confirm'),
    path('password/reset/success/', views.PassResetSuc.as_view(), name='success'),
    path('password/forget/done/', views.PasswordResetDone.as_view(), name='password_reset_done'),
]