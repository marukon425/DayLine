from django.urls import path
from . import views

app_name = 'DayLine_2_top'

urlpatterns = [
    path('', views.TopView.as_view(), name='top'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('terms/', views.Terms.as_view(), name='terms'),
    path('privacy/', views.Privacy.as_view(), name='privacy'),
]
