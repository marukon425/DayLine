from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Event, Color
from .models import *
from .permissions import AUTHORITY_PERMISSIONS, PERM_EVENT_CREATE

import datetime
dt_now = datetime.datetime.now()


class EventFormValidationMixin:
    """
    イベント作成／編集フォームで共通のバリデーションと初期化処理をまとめたミックスイン。

    ブラウザ側のJSやHTMLは開発者ツールで自由に書き換えられるので、
    「選べるルーム」も「日付の前後関係」もサーバー側で必ず検証する。
    """

    def _limit_room_choices(self, user):
        """イベントを作成できる権限があるルームだけを選択肢に出す。"""
        # 権限表から event_create を持つ権限コードを取り出す
        creatable_codes = [
            code for code, perms in AUTHORITY_PERMISSIONS.items()
            if PERM_EVENT_CREATE in perms
        ]
        self.fields["room"].queryset = Room.objects.filter(
            roommember__user=user,
            roommember__authority__authority_code__in=creatable_codes,
        ).distinct().order_by("-is_personal", "room_name")

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        allday = cleaned_data.get("allday")

        if start_date is None:
            # start_dateは必須項目。個別のエラーが既に出ているのでここでは追加しない
            return cleaned_data

        # 終了日が空なら開始日と同じ日として扱う
        # （Noneのまま保存されるとカレンダーAPI側の日付計算で落ちるため）
        if end_date is None:
            end_date = start_date
            cleaned_data["end_date"] = end_date

        if end_date < start_date:
            self.add_error("end_date", "終了日は開始日より後にしてください。")
            return cleaned_data

        # 時間指定イベントで同じ日なら、終了時刻が開始時刻より後である必要がある
        if not allday and start_date == end_date:
            if start_time and end_time and end_time <= start_time:
                self.add_error("end_time", "終了時刻は開始時刻より後にしてください。")

        return cleaned_data


# イベント作成
class CreateEventForm(EventFormValidationMixin, forms.ModelForm):

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
                "placeholder": "タイトルを入力",
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
        self._limit_room_choices(user)


# イベント編集
class EditEventForm(EventFormValidationMixin, forms.ModelForm):

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
        self._limit_room_choices(user)

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
                'style': 'display: none;',  # 隠す
                'class': 'edit-room-icon'
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

#ToDo ※各イベントとDBでつながってるがリレーショナルの関係で独立フォームにする
class ToDoEventForm(forms.ModelForm):
    class Meta:
        model = ToDoEvent
        fields = (
            "event",
            "title",
            #チェックボックスはAjaxで別途更新するからフォームに含めない
        )

        widgets = {
            "event": forms.HiddenInput(attrs={
            }),
            "title": forms.TextInput(attrs={
            })
        }