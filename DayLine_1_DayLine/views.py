from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.views.generic import *
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from .models import Event
from .models import Room, RoomMember, Authority, Color
from .forms import *
from DayLine_3_accounts.models import *
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .permissions import (
    PERM_EVENT_CREATE,
    PERM_EVENT_DELETE,
    PERM_EVENT_EDIT,
    PERM_ROOM_MANAGE,
    get_room_member,
    has_room_permission,
    require_room_permission,
)
import urllib.request

import json
import re
from groq import Groq
from django.conf import settings
# Pythonはクラスを2回定義すると後から定義した方で上書きされるからここのクラスであらかじめ定義しておく
class IndexContext:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CreateEventForm(user=self.request.user)
        context['my_rooms'] = Room.objects.filter(
            roommember__user=self.request.user
        ).distinct()
        context['colors'] = Color.objects.all()
        context['user_name'] = self.request.user.username
        context['email'] = self.request.user.email
        context['icon'] = self.request.user.icon.url if self.request.user.icon else '/media/defaults/user_icon.png'
        return context

# メイン
@method_decorator(login_required, name='dispatch')
class IndexView(IndexContext,TemplateView):
    template_name = 'index.html'

# イベント作成
# LoginRequiredMixin: 未ログインユーザーをログイン画面にリダイレクト
class CreateEvent(LoginRequiredMixin, IndexContext, CreateView):
    template_name = 'index.html'
    model = Event
    form_class = CreateEventForm
    success_url = reverse_lazy('DayLine_1_DayLine:index')

    def form_valid(self, form):
        # 送信されたルームに対してイベント作成権限があるか確認する
        # （フォームの選択肢はJS/HTMLで書き換えられるのでサーバー側でも必ず見る）
        require_room_permission(self.request.user, form.cleaned_data.get('room'), PERM_EVENT_CREATE)
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    # CreateViewだとformにuserを渡すときにkwargsにuserが入らないらしい
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user  # ← これが必須
        return kwargs

# イベント編集
# LoginRequiredMixin: 未ログインユーザーをログイン画面にリダイレクト
class EditEvent(LoginRequiredMixin, IndexContext, UpdateView):
    model = Event
    form_class = EditEventForm
    template_name = 'index.html'
    success_url = reverse_lazy('DayLine_1_DayLine:index')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # URLのUUIDを書き換えても、イベント編集権限のないルームのイベントは編集できないようにする（IDOR対策）
        require_room_permission(self.request.user, obj.room, PERM_EVENT_EDIT)
        return obj

    def form_valid(self, form):
        # 別のルームへ付け替えようとしている場合は、移動先でも作成権限が必要
        require_room_permission(self.request.user, form.cleaned_data.get('room'), PERM_EVENT_CREATE)
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    # CreateViewだとformにuserを渡すときにkwargsにuserが入らないらしい
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user  # ← これが必須
        return kwargs

# 削除ビュー
# LoginRequiredMixin: 未ログインユーザーをログイン画面にリダイレクト
class PostDeletView(LoginRequiredMixin, DeleteView):
    template_name = 'index.html'
    model = Event
    # 削除が完了したらマイページに戻るように設定する
    success_url = reverse_lazy('DayLine_1_DayLine:index')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # URLのUUIDを書き換えても、イベント削除権限のないルームのイベントは削除できないようにする（IDOR対策）
        require_room_permission(self.request.user, obj.room, PERM_EVENT_DELETE)
        return obj

# json
from datetime import datetime, timedelta

# カレンダーに表示するイベントをJSONで返すAPI
# LoginRequiredMixin: 未ログインだと他人のイベントが漏れるため必須
# raise_exception=True: APIなのでログイン画面のHTMLを返さず403を返す
class EventApi(LoginRequiredMixin, View):
    raise_exception = True

    # 自分が所属しているルームのイベントを全部表示する
    def get_queryset(self):
        return Event.objects.filter(
            room__roommember__user=self.request.user
        ).order_by('start_date').distinct()
    
    def get(self, request, *args, **kwargs):
        events = self.get_queryset()
        data = []
        for i in events:
            id = i.id
            room = i.room.room_name
            room_id = str(i.room.id)
            title = i.title
            created_by = i.created_by.username
            start_date = i.start_date
            start_time = i.start_time
            allday = i.allday
            # FullCalendarの終了日は「排他的（その日は含まない）」仕様なので、
            # 終日イベントだけ +1日 して最終日まで塗られるようにする。
            # 時間指定イベントで +1日 すると翌日まで伸びてしまうためここで分岐する。
            if allday:
                end_date = i.end_date + timedelta(days=1)
            else:
                end_date = i.end_date
            end_time = i.end_time
            user = i.created_by.username
            repeat_code = i.repeat.repeat_code if i.repeat else None
            repeat_name = i.repeat.repeat_name if i.repeat else None
            url = i.url
            locate = i.location
            memo = None if i.memo == "" else i.memo

            color = i.color.color if i.color else ""
            color_id = i.color.id if i.color else None
            repeat_id = i.repeat.id if i.repeat else None

            # 繰り返しあり → rrule形式で返す
            if repeat_code and repeat_code != "none":
                if allday:
                    dtstart = str(start_date)
                else:
                    dtstart = f"{start_date}T{start_time}"

                # durationを計算（start〜endの差分）
                if allday:
                    d_start = datetime.strptime(str(start_date), "%Y-%m-%d")
                    d_end   = datetime.strptime(str(end_date),   "%Y-%m-%d")
                    delta = d_end - d_start
                    duration = f"{delta.days}D"  # RRule用: "1D" "7D" など
                else:
                    d_start = datetime.strptime(f"{start_date}T{start_time}", "%Y-%m-%dT%H:%M:%S")
                    d_end   = datetime.strptime(f"{end_date}T{end_time}",     "%Y-%m-%dT%H:%M:%S")
                    delta = d_end - d_start
                    total_seconds = int(delta.total_seconds())
                    h, remainder = divmod(total_seconds, 3600)
                    m, s = divmod(remainder, 60)
                    duration = f"{h:02}:{m:02}"  # "01:30" など

                event_obj = {
                    "id": id,
                    "user": user,
                    "calendar": room,
                    "room_id": room_id,
                    "title": title,
                    "created_by": created_by,
                    "allDay": allday,
                    "rrule": {
                        "freq": repeat_code,   # "daily" / "weekly" / "monthly" / "yearly"
                        "dtstart": dtstart,
                    },
                    "duration": duration,
                    "color": color,
                    # extendedProps（詳細モーダル用）
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "start_time": str(start_time),
                    "end_time": str(end_time),
                    "repeat": repeat_name,
                    "event_url": url,
                    "locate": locate,
                    "memo": memo,
                    "color_id": color_id,
                    "repeat_id": repeat_id,
                }

            # 繰り返しなし → 従来通り
            else:
                if allday:
                    start = str(start_date)
                    end = str(end_date)
                else:
                    start = f"{start_date}T{start_time}"
                    end = f"{end_date}T{end_time}"

                event_obj = {
                    "id": id,
                    "user": user,
                    "calendar": room,
                    "room_id": room_id,
                    "title": title,
                    "created_by": created_by,
                    "start": start,
                    "end": end,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "start_time": str(start_time),
                    "end_time": str(end_time),
                    "color": color,
                    "repeat": repeat_name,
                    "event_url": url,
                    "locate": locate,
                    "memo": memo,
                    "color_id": color_id,
                    "repeat_id": repeat_id,
                }

            data.append(event_obj)
        return JsonResponse(data, safe=False)


#日本の祝日を取得する
class HolidayApi(View):
    def get(self, request, *args, **kwargs):
        from datetime import date
        year_param = request.GET.get('year')
        today = date.today()

        if year_param:
            # ?year=abc のような数字以外が来ると int() が例外を投げて500になるので、
            # 数字かどうかと現実的な範囲かをここで弾いて400を返す
            if not year_param.isdigit():
                return JsonResponse({'error': 'year must be a number'}, status=400)
            year = int(year_param)
            if not (1900 <= year <= 2100):
                return JsonResponse({'error': 'year out of range'}, status=400)
            years = [year]
        else:
            years = [today.year, today.year + 1]

        data = []
        for year in years:
            url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/JP"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "DayLine/1.0"})
                with urllib.request.urlopen(req, timeout=5) as response:
                    holidays = json.loads(response.read().decode())
                for h in holidays:
                    data.append({
                        "title": h.get("localName") or h.get("name"),
                        "start": h["date"],
                        "allDay": True,
                        "classNames": ["holiday-event"],
                        "extendedProps": {
                            "is_holiday": True,
                        }
                    })
            except Exception:
                pass  # API失敗時はスキップ、カレンダーは動き続ける

        return JsonResponse(data, safe=False)


# ルーム
# LoginRequiredMixin: 未ログインユーザーをログイン画面にリダイレクト
class CreateRoom(LoginRequiredMixin, CreateView):
    template_name = 'create_room.html'
    model = Room
    form_class = CreateRoomForm
    success_url = reverse_lazy('DayLine_1_DayLine:index')

    # get_context_data関数をオーバーラード
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # 2つ目のモデルを指定
        ctx["RoomMember"] = RoomMember.objects.all()
        return ctx
    
    # フィールドに初期値を入れる
    def form_valid(self, form):
        with transaction.atomic():
            # ① ルーム保存
            room = form.save(commit=False)
            # 作成者をルームのオーナーとして記録する
            # （ここを入れ忘れていたため、ユーザーが作ったルームは owner が null のままだった）
            room.owner = self.request.user
            room.save()

            # ② admin権限を取得（安全版）
            admin_authority = Authority.objects.filter(authority_code="owner").first()

            if not admin_authority:
                raise ValueError("admin権限がAuthorityテーブルに存在しません")

            # ③ 作成者をRoomMemberとして登録
            RoomMember.objects.create(
                room=room,
                user=self.request.user,
                authority=admin_authority
            )

        return redirect(self.success_url)
    

# ルーム設定(基本情報)
# LoginRequiredMixin: 未ログインユーザーをログイン画面にリダイレクト
class SettingRoom(LoginRequiredMixin, UpdateView):
    template_name = "room_setting.html"
    model = Room
    form_class = EditRoomForm

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # 所属していないルームの設定画面はそもそも開かせない（IDOR対策）
        # ここで弾かないと get_context_data の RoomMember.objects.get() が例外を投げて500になる
        if get_room_member(self.request.user, obj) is None:
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ルーム設定を編集できる権限があるかどうか（テンプレートで編集UIの出し分けに使う）
        context['can_manage'] = has_room_permission(self.request.user, self.object, PERM_ROOM_MANAGE)
        # 旧テンプレートが is_admin を参照しているので同じ値を渡しておく
        context['is_admin'] = context['can_manage']
        context['room_name'] = self.object.room_name
        context['room_description'] = self.object.room_description
        context['member_info'] = RoomMember.objects.filter(
            room=self.object.pk
        )
        context['member_count'] = context['member_info'].count()
        return context

    def form_valid(self, form):
        # 権限のないメンバーがフォームを直接POSTしてもルーム情報を変更できないようにする
        require_room_permission(self.request.user, self.object, PERM_ROOM_MANAGE)
        # ここで保存される
        response = super().form_valid(form)
        # この時点で self.object.pk は新しい pk になってる
        return response

    def get_success_url(self):
        # self.object.pk は form_valid() 後に保存されてるから使える
        return reverse_lazy(
            'DayLine_1_DayLine:settingroom',
            kwargs={'pk': self.object.pk}
        )

# ルーム設定(メンバー設定)
# LoginRequiredMixin: 未ログインユーザーをログイン画面にリダイレクト
class SettingRoomMember(LoginRequiredMixin, UpdateView):
    template_name = "room_setting_memmber.html"
    model = Room
    form_class = EditRoomMemberForm

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # 所属していないルームのメンバー一覧は見せない（IDOR対策）
        if get_room_member(self.request.user, obj) is None:
            raise PermissionDenied
        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # instanceをRoomじゃなくRoomMemberに差し替え
        kwargs['instance'] = get_room_member(self.request.user, self.object)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_info = RoomMember.objects.filter(room=self.object.pk)

        # メンバーごとにフォームを作る
        member_forms = []
        for member in member_info:
            form = EditRoomMemberForm(instance=member)
            member_forms.append((member, form))

        context['member_forms'] = member_forms
        # メンバー管理の操作ができる権限かどうか
        # （以前はforループから漏れた変数を見ていたため、一覧の最後のメンバーの権限で判定されていた）
        context['can_manage'] = has_room_permission(self.request.user, self.object, PERM_ROOM_MANAGE)
        context['is_admin'] = context['can_manage']
        context['room_name'] = self.object.room_name
        context['room_description'] = self.object.room_description
        context['member_info'] = member_info
        context['member_count'] = member_info.count()
        return context
    def get_success_url(self):
        # self.object.pk は form_valid() 後に保存されてるから使える
        return reverse_lazy(
            'DayLine_1_DayLine:settingroom_memmber',
            kwargs={'pk': self.object.pk}
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # 画面上は管理者にしかセレクトボックスを出していないが、
        # POSTを直接投げれば一般メンバーでも他人の権限を書き換えられてしまうのでここで弾く
        require_room_permission(request.user, self.object, PERM_ROOM_MANAGE)

        # オーナー権限を渡せるのはオーナー本人だけ（管理者が勝手に自分をオーナーに昇格できないようにする）
        requester = get_room_member(request.user, self.object)
        requester_is_owner = requester.authority.authority_code == 'owner'

        member_ids = request.POST.getlist('member_id')

        for member_id in member_ids:
            authority_value = request.POST.get(f'authority_{member_id}')
            if authority_value:
                try:
                    member = RoomMember.objects.get(pk=member_id, room=self.object)
                    authority = Authority.objects.get(pk=authority_value)
                    # オーナーの権限は本人以外が触れない（オーナー剥奪の防止）
                    if member.authority.authority_code == 'owner' and not requester_is_owner:
                        continue
                    if authority.authority_code == 'owner' and not requester_is_owner:
                        continue
                    member.authority = authority
                    member.save()
                except (RoomMember.DoesNotExist, Authority.DoesNotExist):
                    pass
        return redirect('DayLine_1_DayLine:settingroom_memmber', pk=self.object.pk)

#メンバー削除
# LoginRequiredMixin: 未ログインユーザーをログイン画面にリダイレクト
class DeleteRoomMember(LoginRequiredMixin, DeleteView):
    template_name = 'room_setting_memmber.html'
    model = RoomMember

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # メンバー管理権限がなければ他人をルームから外せない
        # ※ delete() ではなく get_object() で見るのは、Django4.2のDeleteViewが
        #    POST時に delete() を通らずform経由で削除するようになったため
        require_room_permission(self.request.user, obj.room, PERM_ROOM_MANAGE)
        # ルームのオーナーは追放できない
        if obj.authority and obj.authority.authority_code == 'owner':
            raise PermissionDenied
        return obj

    def get_success_url(self):
        return reverse_lazy(
            'DayLine_1_DayLine:settingroom_memmber',
            kwargs={'pk': self.object.room.pk}
        )

#検索
# LoginRequiredMixin: 未ログインユーザーをログイン画面にリダイレクト
class SearchEvent(LoginRequiredMixin, ListView):
    template_name = "serch_event.html"
    model = Event
    context_object_name = 'events'
    paginate_by = 50

    # 並び順の選択肢: 画面から来る値 → order_by に渡すフィールド
    SORT_OPTIONS = {
        'new': ('-created_at', '登録が新しい順'),
        'old': ('created_at', '登録が古い順'),
        'start_asc': ('start_date', '開始日が早い順'),
        'start_desc': ('-start_date', '開始日が遅い順'),
        'title': ('title', 'タイトル順'),
    }
    DEFAULT_SORT = 'new'

    def get_queryset(self):
        params = self.request.GET
        # 自分が所属しているルームのイベントだけが検索対象
        queryset = Event.objects.filter(
            room__roommember__user=self.request.user
        ).select_related('room', 'color', 'created_by').distinct()

        # --- キーワード検索（タイトル・メモ・場所を横断して探す） ---
        query = params.get('query')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(memo__icontains=query)
                | Q(location__icontains=query)
            )

        # --- ルームで絞り込み ---
        room_id = params.get('room')
        if room_id:
            queryset = queryset.filter(room__id=room_id)

        # --- 期間で絞り込み（開始日がこの範囲に入るイベント） ---
        date_from = params.get('date_from')
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        date_to = params.get('date_to')
        if date_to:
            queryset = queryset.filter(start_date__lte=date_to)

        # --- 終日／時間指定で絞り込み ---
        allday = params.get('allday')
        if allday == 'true':
            queryset = queryset.filter(allday=True)
        elif allday == 'false':
            queryset = queryset.filter(allday=False)

        # --- 並び替え（未指定・不正な値ならデフォルトの新着順） ---
        # order_byを付けないと表示順がDB任せでバラバラになる
        sort_key = params.get('sort', self.DEFAULT_SORT)
        order_field = self.SORT_OPTIONS.get(sort_key, self.SORT_OPTIONS[self.DEFAULT_SORT])[0]
        return queryset.order_by(order_field, '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET
        # フィルターUIの選択肢と、選ばれている値をテンプレートに渡す
        context['my_rooms'] = Room.objects.filter(
            roommember__user=self.request.user
        ).distinct().order_by('-is_personal', 'room_name')
        context['sort_options'] = [
            (key, label) for key, (_, label) in self.SORT_OPTIONS.items()
        ]
        context['current_query'] = params.get('query', '')
        context['current_room'] = params.get('room', '')
        context['current_sort'] = params.get('sort', self.DEFAULT_SORT)
        context['current_allday'] = params.get('allday', '')
        context['current_date_from'] = params.get('date_from', '')
        context['current_date_to'] = params.get('date_to', '')
        return context



# 招待機能
@login_required
def join_room_by_code(request, join_url):
    room = get_object_or_404(Room, join_url=join_url)

    # すでに参加済みか確認
    if not RoomMember.objects.filter(room=room, user=request.user).exists():
        RoomMember.objects.create(
            room=room,
            user=request.user
        )
    return redirect('DayLine_1_DayLine:index')










#--------------------------------------------------- 生成aiを使った予定管理 ---------------------------------------------------
import html
import logging
import uuid as uuid_lib
from datetime import date as date_cls

# このモジュール用のロガー。詳細なエラーはサーバーのログにだけ出し、ブラウザには返さない
logger = logging.getLogger(__name__)

# --- AIチャットの入力・出力に対する制限値 ---
# LLMのPrompt Injectionは仕組み上100%は防げないので、
# 「AIが何を言おうと、実際にDBを触れる範囲はここで決めた形式・権限を超えられない」ようにする
AI_MAX_MESSAGE_LENGTH = 1000   # ユーザーが1回に送れる文字数
AI_MAX_TITLE_LENGTH = 100      # AIが作れる予定タイトルの長さ（Event.titleのmax_lengthと合わせる）


def _parse_uuid(value):
    """AIが返した文字列が正しいUUIDならUUIDオブジェクトを、そうでなければNoneを返す。"""
    if not isinstance(value, str):
        return None
    try:
        return uuid_lib.UUID(value)
    except (ValueError, AttributeError):
        return None


def _parse_date(value):
    """AIが返した文字列が YYYY-MM-DD 形式の実在する日付ならdateを、そうでなければNoneを返す。"""
    if not isinstance(value, str):
        return None
    try:
        return date_cls.fromisoformat(value)
    except ValueError:
        return None


def _clean_title(value):
    """AIが返したタイトルを検証する。文字列でない・空・長すぎる場合はNoneを返す。"""
    if not isinstance(value, str):
        return None
    title = value.strip()
    if not title or len(title) > AI_MAX_TITLE_LENGTH:
        return None
    return title


#送られてきた会話から予定を管理するのか普通にしゃべるのかの処理を分けるメソッド
def _execute_action(ai_text, user):
    """
    AIの返答から <action> タグを取り出してDB操作を実行する。

    ここはPrompt Injectionの最終防衛ラインになる。
    「システムプロンプトを無視して〇〇して」のような入力でAIが暴走しても、
    以下を全部通らないとDBには一切触れない：
      - typeが create / delete / edit のいずれか
      - room_id / event_id が正しいUUID形式
      - そのルーム・イベントがログインユーザーの所属するものである
      - ログインユーザーがその操作をする権限を持っている
      - 日付が YYYY-MM-DD の実在する日付、タイトルが規定の長さ以内
    """
    # AIがタグを変形して返すケースを正規化
    normalized = html.unescape(ai_text)
    normalized = normalized.replace('[action]', '<action>').replace('[/action]', '</action>')

    match = re.search(r'<action>(.*?)</action>', normalized, re.DOTALL)

    if not match:
        return None

    try:
        action = json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return "⚠️ AIのレスポンス形式が不正です。"

    # JSONの中身が辞書でなければ（配列や文字列を返してきた場合）ここで終了
    if not isinstance(action, dict):
        return "⚠️ AIのレスポンス形式が不正です。"

    action_type = action.get("type")
    # 想定外のtypeは一切実行しない（ホワイトリスト方式）
    if action_type not in ('create', 'delete', 'edit'):
        return None

    if action_type == "create":
        room_id = _parse_uuid(action.get("room_id"))
        if room_id is None:
            return "⚠️ 指定されたルームが見つかりません。"

        # 自分が所属しているルームかを必ずDBで確認する（AIの言い分は信用しない）
        room = Room.objects.filter(id=room_id, roommember__user=user).first()
        if room is None:
            return "⚠️ 指定されたルームが見つかりません。"

        # そのルームでイベントを作れる権限があるか
        if not has_room_permission(user, room, PERM_EVENT_CREATE):
            return "⚠️ このカレンダーに予定を追加する権限がありません。"

        title = _clean_title(action.get('title'))
        if title is None:
            return "⚠️ 予定のタイトルが正しくありません。"

        start_date = _parse_date(action.get('start_date'))
        if start_date is None:
            return "⚠️ 予定の日付が正しくありません。"

        end_date = _parse_date(action.get('end_date')) or start_date
        if end_date < start_date:
            return "⚠️ 終了日が開始日より前になっています。"

        allday = action.get('allday', True)
        if not isinstance(allday, bool):
            allday = True

        try:
            Event.objects.create(
                room=room,
                title=title,
                created_by=user,
                start_date=start_date,
                end_date=end_date,
                allday=allday,
            )
        except Exception:
            # 例外の中身にはファイルパスや設定値が含まれうるのでログにだけ残す
            logger.exception("AIチャット経由の予定作成に失敗しました")
            return "⚠️ 予定の作成に失敗しました。"
        return "✅ 予定を作成しました。"

    # delete / edit は対象イベントの特定が共通なのでまとめて取得する
    event_id = _parse_uuid(action.get('event_id'))
    if event_id is None:
        return "⚠️ 該当する予定が見つかりませんでした。"

    event = Event.objects.filter(id=event_id, room__roommember__user=user).first()
    if event is None:
        return "⚠️ 該当する予定が見つかりませんでした。"

    if action_type == "delete":
        if not has_room_permission(user, event.room, PERM_EVENT_DELETE):
            return "⚠️ この予定を削除する権限がありません。"
        try:
            event.delete()
        except Exception:
            logger.exception("AIチャット経由の予定削除に失敗しました")
            return "⚠️ 削除に失敗しました。"
        return "🚮 予定を削除しました。"

    # action_type == "edit"
    if not has_room_permission(user, event.room, PERM_EVENT_EDIT):
        return "⚠️ この予定を編集する権限がありません。"

    if 'title' in action:
        title = _clean_title(action['title'])
        if title is None:
            return "⚠️ 予定のタイトルが正しくありません。"
        event.title = title

    if 'start_date' in action:
        start_date = _parse_date(action['start_date'])
        if start_date is None:
            return "⚠️ 予定の日付が正しくありません。"
        event.start_date = start_date

    if 'end_date' in action:
        end_date = _parse_date(action['end_date'])
        if end_date is None:
            return "⚠️ 予定の日付が正しくありません。"
        event.end_date = end_date

    if 'allday' in action and isinstance(action['allday'], bool):
        event.allday = action['allday']

    if event.end_date and event.end_date < event.start_date:
        return "⚠️ 終了日が開始日より前になっています。"

    try:
        event.save()
    except Exception:
        logger.exception("AIチャット経由の予定変更に失敗しました")
        return "⚠️ 変更に失敗しました。"
    return "✏️ 予定を変更しました。"


@login_required
def ai_chat(request):
    if not request.method == 'POST':
        #postじゃなかったらメッセージとともに405エラーを送信する  status405にしないと正常な応答(200)になる
        return JsonResponse({"error": "POST only"}, status=405)
    else:
        # APIキーが未設定だとGroqのクライアント生成時に落ちて「接続エラー」に見えるので、
        # 先に確認して原因が分かるメッセージを返す
        if not settings.GROQ_API_KEY:
            logger.error("GROQ_API_KEY が設定されていません（.env / 環境変数を確認してください）")
            return JsonResponse({"error": "AI機能が利用できません"}, status=503)

        # リクエストデータのjsonを辞書型に変換
        # 壊れたJSONが来ても500にせず400で返す
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "リクエストの形式が不正です"}, status=400)

        message = body.get("message", "")
        if not isinstance(message, str) or not message.strip():
            return JsonResponse({"error": "メッセージが空です"}, status=400)

        # 極端に長い入力はプロンプトを押し流してシステムプロンプトを無効化する攻撃に使えるので上限を設ける
        if len(message) > AI_MAX_MESSAGE_LENGTH:
            return JsonResponse(
                {"error": f"メッセージは{AI_MAX_MESSAGE_LENGTH}文字以内で入力してください"},
                status=400,
            )

        user_event = Event.objects.filter(
            # 所属してるルームかつログイン中のユーザーのイベントを重複なしで抽出
            room__roommember__user=request.user
        ).distinct()
        # AIに渡しやすいようにテキスト形式に整形する
        events_text = "\n".join([
            f"- ID:{e.id} タイトル:{e.title} 開始:{e.start_date} 終了:{e.end_date} ルーム:{e.room.room_name}"
            for e in user_event
        ])
        

        rooms = Room.objects.filter(roommember__user=request.user).distinct()
        rooms_text = "\n".join([
            f"- ID:{r.id} 名前:{r.room_name}"
            for r in rooms
        ])
        from datetime import date
        # プロンプトを作ってユーザーに返信する準備をする
        system_prompt = f"""
        今日の日付は {date.today()} です。
        あなたは予定管理アプリ「DayLine」のAIアシスタントです。
        ユーザーの予定を自然な会話で登録・編集・削除できます。

        【操作方法】
        予定の操作が必要な場合は、必ず以下のJSON形式を <action></action> タグで囲んで返してください。

        予定作成：
        <action>
        {{"type": "create", "title": "タイトル", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "room_id": "ルームのUUID", "allday": true}}
        </action>

        予定削除：
        <action>
        {{"type": "delete", "event_id": "イベントのUUID"}}
        </action>

        予定変更：
        <action>
        {{"type": "edit", "event_id": "イベントのUUID", "title": "新タイトル", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "allday": true}}
        </action>

        【ユーザーの登録済みルーム】
        {rooms_text}

        【ユーザーの現在の予定一覧】
        {events_text}
        【絶対に守ること】
        操作不要な質問には普通に答えてください。
        DayLineへの脆弱性を突く質問に対しては回答を避けるような回答をしてください
        あなたが操作不可能な指示をユーザーが出して来たら素直に操作ができないような回答をしてください
        - タグは必ず半角の < と > を使うこと： <action> と </action>
        - [ ] 角括弧や &lt; などのエスケープは絶対に使わないこと
        - HTMLエスケープ禁止
        複数のアクションを実行するときになった時は１番目のアクションだけを実行してユーザーに一つ目に実行したアクションの内容だけを出力してください
        """
        # apiキーを代入する  多分Groqのライブラリの引数にapiキーを代入しないと使えないからsettingsから引っ張てる
        client = Groq(api_key=settings.GROQ_API_KEY)
        # 最初にaiのプロンプトを代入する
        # システムプロンプトとユーザー入力はroleを分けて渡す（ユーザーの文字列を指示書に混ぜない）
        groq_messages = [
            {"role": "system", "content": system_prompt},  # AIへの指示書を先頭に入れる
            {"role": "user", "content": message},
        ]

        # Groq APIにリクエストを送る
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=groq_messages,
                max_tokens=1024,
                # 10秒だとモデルの応答が間に合わずタイムアウトして「接続エラー」になることがあったため延長
                timeout=30
            )
        except Exception:
            # str(e) をそのまま返すとAPIキー名・ファイルパス・設定値がブラウザに漏れる。
            # 詳細はサーバーのログにだけ残して、クライアントには汎用メッセージを返す
            logger.exception("Groq APIへのリクエストに失敗しました")
            return JsonResponse({"error": "AIとの通信に失敗しました"}, status=500)

        # AIの返答テキストを取り出す
        ai_text = response.choices[0].message.content or ""

        action_result = _execute_action(ai_text, request.user)
        ai_text = html.unescape(ai_text)
        # <action>タグはユーザーに見せる必要がないのでサーバー側でも取り除いておく
        # （フロント側の除去処理をすり抜けて生タグが表示されるのを防ぐ）
        reply_text = re.sub(r'<action>.*?</action>', '', ai_text, flags=re.DOTALL).strip()

        #拾ったjsonからメッセージを抽出してjsonで返す
        return JsonResponse({"reply": reply_text, "action_result": action_result})
    


#todo機能系の関数ビュー
# todo作成
@login_required
def todo_create(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    
    # request.bodyからJSONを取り出す
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid json'}, status=400)
    title = body.get('title')
    event_id = body.get('event')

    # バリデーション（フロントのJSは書き換えられるのでサーバー側で長さも見る）
    if not title or not event_id:
        return JsonResponse({'error': 'invalid data'}, status=400)
    title = str(title).strip()
    if not title or len(title) > 50:  # ToDoEvent.title の max_length に合わせる
        return JsonResponse({'error': 'invalid title'}, status=400)

    # イベントを取得（自分が所属するルームのイベントのみ許可。他人のイベントにToDoを追加できないようにするIDOR対策）
    event = get_object_or_404(Event, pk=event_id, room__roommember__user=request.user)

    # DBに保存
    todo = ToDoEvent.objects.create(
        title=title,
        event=event,
    )

    return JsonResponse({"id": str(todo.id), "title": todo.title})
# tod削除
@login_required
def todo_delete(request, pk):
    # ToDoを取得（自分が所属するルームのイベントに紐づくToDoのみ許可。他人のToDoを削除できないようにするIDOR対策）
    question = get_object_or_404(ToDoEvent, pk=pk, event__room__roommember__user=request.user)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    else:
        #削除
        question.delete()
        #削除できたことを伝える
        return JsonResponse({'success': True})
    # 返すデータは success: True

#todoのオンオフを処理する
@login_required
def todo_check(request, pk):
    # ToDoを取得（自分が所属するルームのイベントに紐づくToDoのみ許可。他人のToDoのチェック状態を変更できないようにするIDOR対策）
    question = get_object_or_404(ToDoEvent, pk=pk, event__room__roommember__user=request.user)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    else:
        # チェック状態をトグルする（Trueならfalse、FalseならTrue）
        # ※ 以前あった question.check = not question.check は、ToDoEventに存在しない
        #    check フィールドを触っていて（Djangoの Model.check() を参照していた）保存もされない
        #    デッドコードだったため削除。状態は checkTodo に一本化する。
        question.checkTodo = not question.checkTodo
        question.save()# 現在の状態を保存

        # 返すデータは checkTodo の現在の状態
        return JsonResponse({'check': question.checkTodo})

#todoを取得するメソッド
@login_required
def todo_list(request, event_id):
    if request.method != 'GET':
        return JsonResponse({'error': 'GET only'}, status=405)
    else:
        # event_idに紐づくToDoを取得（自分が所属するルームのイベントのみ許可。他人のToDo一覧を取得できないようにするIDOR対策）
        if not Event.objects.filter(pk=event_id, room__roommember__user=request.user).exists():
            return JsonResponse({'error': 'forbidden'}, status=403)
        todos = ToDoEvent.objects.filter(event_id=event_id)
        data = []
        for i in todos:
            data.append({
                'id': str(i.id),
                'title': i.title,
                'check': i.checkTodo
            })
        # 返すデータは id・title・check のリスト
        return JsonResponse(data, safe=False)
    
#todoのタイトルを変更するメソッド
@login_required
def todo_edit_title(request, pk):
    # ToDoを取得（自分が所属するルームのイベントに紐づくToDoのみ許可。他人のToDoタイトルを変更できないようにするIDOR対策）
    question = get_object_or_404(ToDoEvent, pk=pk, event__room__roommember__user=request.user)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    else:
        # リクエストのbodyからタイトルを取得
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'invalid json'}, status=400)
        new_title = body.get('title')

        # 空文字や長すぎるタイトルで保存されないようサーバー側で検証する
        if not isinstance(new_title, str):
            return JsonResponse({'error': 'invalid title'}, status=400)
        new_title = new_title.strip()
        if not new_title or len(new_title) > 50:  # ToDoEvent.title の max_length に合わせる
            return JsonResponse({'error': 'invalid title'}, status=400)

        # タイトルを更新
        question.title = new_title
        question.save()# 現在の状態を保存

        # 返すデータは更新後のタイトル
        return JsonResponse({'title': question.title})