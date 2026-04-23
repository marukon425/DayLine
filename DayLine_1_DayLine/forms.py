from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Event, Color
from .models import *

import datetime
dt_now = datetime.datetime.now()


# イベント作成
class CreateEventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = (
            "room",
            "title",
            "start_date",
            "end_date",
            "start_time",
            "end_time",
            "allday",
            "color",
            "repeat",
            "url",
            "location",
            "memo"
        )

        widgets = {
            "room": forms.HiddenInput(attrs={
                "class": "custom-select-value"
            }),
            "title": forms.TextInput(attrs={
                "placeholder": "title",
                "class":"id_title"
            }),
            "start_date": forms.DateInput(attrs={
                'class': 'create-datetime-input date-picker start-date',
                'type': 'text',
                'style':'width:100px;',
            }),
            "end_date": forms.DateInput(attrs={
                'class': 'create-datetime-input date-picker end-date',
                'type': 'text',
                'value': dt_now.strftime('%Y-%m-%d'),
                'style':'width:100px;'
            }),
            "start_time": forms.TimeInput(attrs={
                'class': 'create-datetime-input time-picker',
                'type': 'text',
                'style':'width:100px;'
            }),
            "end_time": forms.TimeInput(attrs={
                'class': 'create-datetime-input time-picker',
                'type': 'text',
                'style':'width:100px;'
            }),
            "allday": forms.CheckboxInput(attrs={
                "class":"event-allday"
            }),
            "color": forms.HiddenInput(attrs={
                "class": "custom-select-value"
            }),
            "repeat": forms.HiddenInput(attrs={
                "class": "custom-select-value"
            }),
            "url": forms.URLInput(attrs={
                "class": "create-url other-options",
                "placeholder": "https://example.com"
            }),
            "location": forms.TextInput(attrs={
                "class": "create-url other-options",
                "placeholder": "場所"
            }),
            "memo": forms.Textarea(attrs={
                "class": "modal-texterea-form",
                "placeholder": "メモを入力"
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        self.fields["room"].queryset = Room.objects.filter(
            roommember__user=user
        ).distinct().order_by("-is_personal", "room_name")


# イベント編集
class EditEventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = (
            "room",
            "title",
            "start_date",
            "end_date",
            "start_time",
            "end_time",
            "allday",
            "color",
            "repeat",
            "url",
            "location",
            "memo"
        )

        widgets = {
            "room": forms.HiddenInput(attrs={
                "class": "custom-select-value"
            }),
            "title": forms.TextInput(attrs={
                "placeholder": "title",
                "class":"id_title"
            }),
            "start_date": forms.DateInput(attrs={
                'class': 'create-datetime-input start-date',
                'type': 'date',
            }),
            "end_date": forms.DateInput(attrs={
                'class': 'create-datetime-input end-date',
                'type': 'date',
                'value': dt_now.strftime('%Y-%m-%d')
            }),
            "start_time": forms.TimeInput(attrs={
                'class': 'create-datetime-input',
                'type': 'time'
            }),
            "end_time": forms.TimeInput(attrs={
                'class': 'create-datetime-input',
                'type': 'time'
            }),
            "allday": forms.CheckboxInput(attrs={
                "class":"event-allday"
            }),
            "color": forms.HiddenInput(attrs={
                "class": "custom-select-value"
            }),
            "repeat": forms.HiddenInput(attrs={
                "class": "custom-select-value"
            }),
            "url": forms.URLInput(attrs={
                "class": "create-url other-options",
                "placeholder": "https://example.com"
            }),
            "location": forms.TextInput(attrs={
                "class": "create-url other-options",
                "placeholder": "場所"
            }),
            "memo": forms.Textarea(attrs={
                "class": "modal-texterea-form",
                "placeholder": "メモを入力"
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        self.fields["room"].queryset = Room.objects.filter(
            roommember__user=user
        ).distinct().order_by("-is_personal", "room_name")

        # 追加
        self.fields["start_time"].required = False
        self.fields["end_time"].required = False

# ルーム作成
class CreateRoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = (
            "room_name",
            "room_description",
        )

        widgets = {
            "room_name":forms.TextInput(attrs={
                "id":"room-name",
                "placeholder":"カレンダーの名前を入力"
            }),
            "room_description":forms.Textarea(attrs={
                "id":"room-info",
                "placeholder":"説明"
            }),

        }

# ルーム編集(基本情報)
class EditRoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = (
            "room_name",
            "room_description",
            "room_img",
        )

        widgets = {
            "room_name": forms.TextInput(attrs={
                "id": "room-name",
                "placeholder": "カレンダーの名前を入力"
            }),
            "room_description": forms.Textarea(attrs={
                "id": "room-info",
                "placeholder": "説明"
            }),
            'room_img': forms.FileInput(attrs={
                'style': 'display: none;'  # 隠す
            })
        }

# ルーム編集(メンバー管理)
class EditRoomMemberForm(forms.ModelForm):
    class Meta:
        model = RoomMember
        fields = ["authority"]

        widgets = {
            "authority": forms.Select(attrs={
                "class": "form-control",
                "id": "authority",
            })
        }
