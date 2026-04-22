from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'DayLine_3_accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('account/settings/', views.Account_setting.as_view(), name='settings'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('password/forget', views.PassForget.as_view(), name='passfor'),
    path('password/reset/<uidb64>/<token>/', views.PassReset, name='passres'),
    path('password/reset/success', views.PassResetSuc.as_view(), name='success'),
    path('password/forget/done', views.PasswordResetDone.as_view(), name='password_reset_done'), #追加
    
]