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
from django.shortcuts import redirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
import urllib.request

import json
import re
from groq import Groq
from django.conf import settings
# Create your views here.

'''
【 get_context_data 】
テンプレートにデータを渡すための関数( {{○○}}見たな感じの奴 )
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs) # はじめに継承元のメソッドを呼び出す
    context["foo"] = "bar"
    return context


【 get_queryset 】


'''

# メイン
@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'index.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CreateEventForm(user=self.request.user)
        context['my_rooms'] = Room.objects.filter(
            roommember__user=self.request.user
        ).distinct()
        context['colors'] = Color.objects.all()
        context['user_name'] = self.request.user.username
        context["email"] = self.request.user.email
        context["icon"] = self.request.user.icon.url if self.request.user.icon else '/media/defaults/user_icon.png'
        return context

    # prefix="create"

# イベント作成
class CreateEvent(CreateView):
    template_name = 'index.html'
    model = Event
    form_class = CreateEventForm
    success_url = reverse_lazy('DayLine_1_DayLine:index')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_rooms'] = Room.objects.filter(
            roommember__user=self.request.user
        ).distinct()

        context['colors'] = Color.objects.all()
        context['user_name'] = self.request.user.username
        context["email"] = self.request.user.email
        context["icon"] = self.request.user.icon.url if self.request.user.icon else '/media/defaults/user_icon.png'

        return context

    # CreateViewだとformにuserを渡すときにkwargsにuserが入らないらしい
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user  # ← これが必須
        return kwargs

# イベント編集
class EditEvent(UpdateView):
    model = Event
    form_class = EditEventForm
    template_name = 'index.html'
    success_url = reverse_lazy('DayLine_1_DayLine:index')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_rooms'] = Room.objects.filter(
            roommember__user=self.request.user
        ).distinct()

        context['colors'] = Color.objects.all()
        context['user_name'] = self.request.user.username
        context["email"] = self.request.user.email

        return context

    # CreateViewだとformにuserを渡すときにkwargsにuserが入らないらしい
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user  # ← これが必須
        return kwargs

# 削除ビュー
class PostDeletView(DeleteView):
    template_name = 'index.html'
    model = Event
    # 削除が完了したらマイページに戻るように設定する
    success_url = reverse_lazy('DayLine_1_DayLine:index')
    def delete(self, reqest, *args, **kwargs):
        return super().delete(reqest, *args, **kwargs)

# json
from datetime import datetime, timedelta
class EventApi(View):
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
            end_date = i.end_date + timedelta(days=1)
            end_time = i.end_time
            allday = i.allday
            user = i.created_by.username
            repeat_code = i.repeat.repeat_code if i.repeat else None
            repeat_name = i.repeat.repeat_name if i.repeat else None
            url = i.url
            locate = i.location
            memo = None if i.memo == "" else i.memo

            color = i.color.color if i.color else ""

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
                }

            data.append(event_obj)
        return JsonResponse(data, safe=False)


#日本の祝日を取得する
class HolidayApi(View):
    def get(self, request, *args, **kwargs):
        from datetime import date
        year_param = request.GET.get('year')

        if year_param:
            years = [int(year_param)]
        else:
            today = date.today()
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
class CreateRoom(CreateView):
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
    

#日本の祝日を取得する
class HolidayApi(View):
    def get(self, request, *args, **kwargs):
        from datetime import date
        year_param = request.GET.get('year')

        if year_param:
            years = [int(year_param)]
        else:
            today = date.today()
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
class CreateRoom(CreateView):
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
class SettingRoom(UpdateView):
    template_name = "room_setting.html"
    model = Room
    form_class = EditRoomForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = RoomMember.objects.get(
            user=self.request.user,
            room=self.object
        )
        context['is_admin'] = member.authority.authority_code in ["admin", "owner"]
        context['room_name'] = self.object.room_name
        context['room_description'] = self.object.room_description
        context['member_info'] = RoomMember.objects.filter(
            room=self.object.pk
        )
        context['member_count'] = context['member_info'].count()
        return context

    def form_valid(self, form):
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
class SettingRoomMember(UpdateView):
    template_name = "room_setting_memmber.html"
    model = Room
    form_class = EditRoomMemberForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # instanceをRoomじゃなくRoomMemberに差し替え
        kwargs['instance'] = RoomMember.objects.get(
            user=self.request.user,
            room=self.object
        )
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
        context['member_count'] = member_info.count()
        # ...他のcontextも同様
        context['is_admin'] = member.authority.authority_code in ["admin", "owner"]
        context['room_name'] = self.object.room_name
        context['room_description'] = self.object.room_description
        context['member_info'] = RoomMember.objects.filter(room=self.object.pk)
        context['member_count'] = context['member_info'].count()
        return context
    def get_success_url(self):
        # self.object.pk は form_valid() 後に保存されてるから使える
        return reverse_lazy(
            'DayLine_1_DayLine:settingroom_memmber',
            kwargs={'pk': self.object.pk}
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        member_ids = request.POST.getlist('member_id')
        
        for member_id in member_ids:
            authority_value = request.POST.get(f'authority_{member_id}')
            if authority_value:
                try:
                    member = RoomMember.objects.get(pk=member_id, room=self.object)
                    authority = Authority.objects.get(pk=authority_value)
                    member.authority = authority
                    member.save()
                except (RoomMember.DoesNotExist, Authority.DoesNotExist):
                    pass
        return redirect('DayLine_1_DayLine:settingroom_memmber', pk=self.object.pk)

#メンバー削除
class DeleteRoomMember(DeleteView):
    template_name = 'room_setting_memmber.html'
    model = RoomMember

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        requester = RoomMember.objects.get(room=self.object.room, user=request.user)
        
        if requester.authority.authority_code not in ['owner', 'admin']:
            raise PermissionDenied
        
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'DayLine_1_DayLine:settingroom_memmber',
            kwargs={'pk': self.object.room.pk}
        )

#検索
class SearchEvent(ListView):
    template_name = "serch_event.html"
    model = Event
    def get_queryset(self):
        query = self.request.GET.get('query')
        queryset = Event.objects.filter(
            room__roommember__user=self.request.user
        ).distinct()
        if query:
            event_list = queryset.filter(
                title__icontains=query
            )
        else:
            event_list = queryset.all()
        return event_list



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
"""
request.method   # "GET" や "POST" などのHTTPメソッド
request.body     # リクエストのボディ（バイト型の生データ）
request.user     # ログイン中のユーザー
request.GET      # GETパラメータ（URLの?以降）
request.POST     # フォームのPOSTデータ
"""
import html
#送られてきた会話から予定を管理するのか普通にしゃべるのかの処理を分けるメソッド
def _execute_action(ai_text, user):
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

    action_type = action.get("type")

    if action_type == "create":
        try:
            room = Room.objects.get(
                id=action["room_id"],
                roommember__user=user
            )
            Event.objects.create(
                room=room,
                title=action['title'],
                created_by=user,
                start_date=action['start_date'],
                end_date=action.get('end_date', action['start_date']),
                allday=action.get('allday', True),
            )
            return "✅ 予定を作成しました。"
        except Room.DoesNotExist:
            return "⚠️ 指定されたルームが見つかりません。"
        except Exception as e:
            return f"⚠️ 予定の作成に失敗しました: {str(e)}"

    elif action_type == "delete":
        try:
            event = Event.objects.get(
                id=action['event_id'],
                room__roommember__user=user
            )
            event.delete()
            return "🚮 予定を削除しました。"
        except Event.DoesNotExist:
            return "⚠️ 該当する予定が見つかりませんでした。"
        except Exception as e:
            return f"⚠️ 削除に失敗しました: {str(e)}"
    elif action_type == "edit":
        try:
            event = Event.objects.get(
                id=action['event_id'],
                room__roommember__user=user
            )
            if 'title' in action:
                event.title = action['title']
            if 'start_date' in action:
                event.start_date = action['start_date']
            if 'end_date' in action:
                event.end_date = action['end_date']
            if 'allday' in action:
                event.allday = action['allday']
            event.save()
            return "✏️ 予定を変更しました。"
        except Event.DoesNotExist:
            return "⚠️ 該当する予定が見つかりませんでした。"
        except Exception as e:
            return f"⚠️ 変更に失敗しました: {str(e)}"
    return None
"""
re.search(パターン, 探す対象の文字列, オプション)
```

---

パターンの `r'<action>(.*?)</action>'` を分解するとこう。
```
<action>   ← この文字列を探す
(.*?)      ← 何でもいい文字列を取得（これが「中身」）
</action>  ← この文字列で終わる
```

`.*?` の意味はこう。
- `.` = 改行以外の任意の1文字
- `*` = 0回以上繰り返す
- `?` = 最小マッチ（最初に見つかったとこで止まる）

---

`re.DOTALL` は `.` を改行にもマッチさせるオプション。これがないとJSONが複数行になってたとき取れない。

---

つまりAIがこんな返答をしたとき：
```
予定を作成します。
<action>
{"type": "create", "title": "会議"}
</action>
```

`match.group(1)` でこれが取れる：
```
{"type": "create", "title": "会議"}
"""

import logging

# ログの設定（行番号を出力するように設定）
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s [line:%(lineno)d]')

logging.info("処理を開始します")  # 行番号が表示される


@login_required
def ai_chat(request):
    if not request.method == 'POST':
        #postじゃなかったらメッセージとともに405エラーを送信する  status405にしないと正常な応答(200)になる
        return JsonResponse({"error": "POST only"}, status=405)
    else:
        user_event = Event.objects.filter(
            # 所属してるルームかつログイン中のユーザーのイベントを重複なしで抽出
            room__roommember__user=request.user
        ).distinct()
        print(user_event)
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
        groq_messages = [
        {"role": "system", "content": system_prompt}  # AIへの指示書を先頭に入れる
        ]

        # リクエストデータをjsonを辞書型に変換
        body = json.loads(request.body)
        message = body.get("message", "")

        # ユーザーのメッセージを代入
        groq_messages.append(
            {"role": "user", "content": message}
        )

        # Groq APIにリクエストを送る
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=groq_messages,
                max_tokens=1024,
                timeout=10
            )
        except Exception as e:
            print(f"エラー: {e}")
            return JsonResponse({"error": str(e)}, status=500)
        
        # AIの返答テキストを取り出す
        ai_text = response.choices[0].message.content
        print(repr(ai_text))  # repr()でエスケープ文字も見える

        action_result = _execute_action(ai_text, request.user)
        ai_text = html.unescape(ai_text)
        #拾ったjsonからメッセージを抽出してjsonで返す
        return JsonResponse({"reply": ai_text, "action_result": action_result})
    
