from django.urls import path
from . import views
from DayLine_3_accounts.views import Profile_Api

app_name = 'DayLine_1_DayLine'

urlpatterns = [
    # カレンダー
    path('', views.IndexView.as_view(), name='index'),
    path('event/create/', views.CreateEvent.as_view(), name='create'),
    path('event/<uuid:pk>/edit/', views.EditEvent.as_view(), name='edit'),
    path('event/<uuid:pk>/delete/', views.PostDeletView.as_view(), name = 'event_delete'),
    path('createroom/', views.CreateRoom.as_view(), name='createroom'),
    path('settingroom/<uuid:pk>/', views.SettingRoom.as_view(), name='settingroom'),
    path('json/userevent/', views.EventApi.as_view(), name='events_jspm'),
    path('json/userinfo/', Profile_Api.as_view(), name='profile_api'),
    path('room/join/<str:join_url>/', views.join_room_by_code, name='join_room_by_code'),
    path('event/search/', views.SearchEvent.as_view(), name='search_event'),
    path('ai/api/', views.ai_chat, name='ai_chat'),
    path('settingroom/memmber/<uuid:pk>/', views.SettingRoomMember.as_view(), name='settingroom_memmber'),
    path('settingroom/memmber/delete/<uuid:pk>/', views.DeleteRoomMember.as_view(), name='settingroom_memmber_delete'),
    path('json/holidays/', views.HolidayApi.as_view(), name='holidays_api'),
    path('json/todo/create/', views.todo_create, name='todo_create'),
    path('json/todo/delete/<uuid:pk>/', views.todo_delete, name='todo_delete'),
    path('json/todo/check/<uuid:pk>/', views.todo_check, name='todo_check'),
    path('json/todo/list/<uuid:event_id>/', views.todo_list, name='todo_list'),

]

# http://127.0.0.1:8000/index/room/join/5fcf91100a/
