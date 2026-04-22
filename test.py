# ☆クロード☆
#調べても分からないからcloadに生成
"""
処理の流れ
① フロント → メッセージ送信（JSON）
② Django → 受け取る
③ DBから予定・ルーム取得
④ system_promptに埋め込む
⑤ Geminiに送信
⑥ AIが返信（＋JSON）
⑦ <action>を抽出
⑧ DB操作（作成・削除）
⑨ 結果をフロントに返す
"""
# -----------------------------------------------
# 必要なライブラリをインポート
# -----------------------------------------------
import json                    # JSONの読み書き
import re                      # 正規表現（文字列の検索・抽出）
from groq import Groq
from django.conf import settings  # settings.pyの値を読み込む
# -----------------------------------------------
# AIチャット用のView関数
# -----------------------------------------------
@login_required
def ai_chat(request):

    # POSTリクエスト以外は弾く
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    # -----------------------------------------------
    # フロントから送られてきたデータを取り出す
    # -----------------------------------------------
    # request.body → フロントからのJSONデータ（バイト型）
    # json.loads()  → バイト型のJSONをPythonの辞書型に変換
    body = json.loads(request.body)

    # ユーザーが入力したメッセージ
    user_message = body.get("message", "")

    # 過去の会話履歴（フロントのJSで管理して毎回送ってもらう）
    # Geminiはサーバー側で会話を記憶しないのでフロントから毎回渡す必要がある
    history = body.get("history", [])

    # -----------------------------------------------
    # ユーザーの予定・ルーム一覧をDBから取得してAIに渡す
    # -----------------------------------------------
    events = Event.objects.filter(
        #sqlの文法でアンダースコアを使うらしい
        room__roommember__user=request.user
    ).order_by("start_date").distinct()[:50]

    # AIに渡しやすいようにテキスト形式に整形する
    events_text = "\n".join([
        f"- ID:{e.id} タイトル:{e.title} 開始:{e.start_date} 終了:{e.end_date} ルーム:{e.room.room_name}"
        for e in events
    ])

    rooms = Room.objects.filter(roommember__user=request.user).distinct()
    rooms_text = "\n".join([
        f"- ID:{r.id} 名前:{r.room_name}"
        for r in rooms
    ])

    # -----------------------------------------------
    # システムプロンプト（AIへの指示書）を作成
    # -----------------------------------------------
    system_prompt = f"""
あなたはカレンダーアプリ「DayLine」のAIアシスタントです。
ユーザーの予定を自然な会話で登録・確認・削除できます。

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

【ユーザーの登録済みルーム】
{rooms_text}

【ユーザーの現在の予定一覧】
{events_text}

操作不要な質問には普通に日本語で答えてください。
"""

# -----------------------------------------------
    # Groq APIを呼び出す
    # -----------------------------------------------
    # GroqのクライアントをAPIキーで初期化する
    client = Groq(api_key=settings.GROQ_API_KEY)

    # -----------------------------------------------
    # 会話履歴をGroq用の形式に変換する
    # -----------------------------------------------
    # Groqは OpenAI互換のフォーマットなので role は "user" / "assistant" のままでOK
    # システムプロンプトを先頭に追加して、その後に会話履歴を続ける
    groq_messages = [
        {"role": "system", "content": system_prompt}  # AIへの指示書を先頭に入れる
    ]

    # 過去の会話履歴をそのまま追加（roleの変換不要）
    for msg in history:
        groq_messages.append({
            "role": msg["role"],       # "user" or "assistant" そのまま使える
            "content": msg["content"]
        })

    # 今回のユーザーメッセージを末尾に追加
    groq_messages.append({
        "role": "user",
        "content": user_message
    })

    # Groq APIにリクエストを送る
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Groqで使える無料モデル
        messages=groq_messages,
        max_tokens=1024
    )

    # AIの返答テキストを取り出す
    ai_text = response.choices[0].message.content
    # <action>タグがあればDB操作を実行する
    action_result = _execute_action(ai_text, request.user)

    # フロントにJSONで返す
    return JsonResponse({
        "reply": ai_text,
        "action_result": action_result
    })


# -----------------------------------------------
# AIの返答からDB操作を実行する関数
# -----------------------------------------------
def _execute_action(ai_text, user):
    """
    AIの返答テキストの中に <action>...</action> タグがあれば
    その中のJSONを読み取って予定の作成・削除を実行する
    """

    # re.search() → 文字列の中から正規表現にマッチする部分を探す
    # <action>と</action>の間の文字列を抽出する
    # re.DOTALL → 改行も含めてマッチさせる
    match = re.search(r'<action>(.*?)</action>', ai_text, re.DOTALL)

    # <action>タグが見つからなければ何もしない
    if not match:
        return None

    try:
        # match.group(1) → ()の中にマッチした部分（JSONの文字列）
        # json.loads()   → JSON文字列をPythonの辞書型に変換
        action = json.loads(match.group(1).strip())
        action_type = action.get("type")

        # -----------------------------------------------
        # 予定の作成
        # -----------------------------------------------
        if action_type == "create":
            # 指定されたroom_idのルームを取得
            # roommember__user=user → 自分が所属しているルームのみ許可（セキュリティ対策）
            room = Room.objects.get(
                id=action["room_id"],
                roommember__user=user
            )
            Event.objects.create(
                room=room,
                title=action["title"],
                start_date=action["start_date"],
                # end_dateが省略された場合はstart_dateと同じ日にする
                end_date=action.get("end_date", action["start_date"]),
                allday=action.get("allday", True),
                created_by=user
            )
            return "✅ 予定を作成しました"

        # -----------------------------------------------
        # 予定の削除
        # -----------------------------------------------
        elif action_type == "delete":
            # 自分のルームの予定のみ削除可能（セキュリティ対策）
            event = Event.objects.get(
                id=action["event_id"],
                room__roommember__user=user
            )
            event.delete()
            return "🗑️ 予定を削除しました"

    except Exception as e:
        # DB操作中にエラーが起きたらエラーメッセージを返す
        return f"⚠️ 操作に失敗しました: {str(e)}"

    return None





    # ai_chat というView関数を追加する
    # ユーザーが /index/ai/chat/ にPOSTしたときにai_chat関数が呼ばれる
    # ☆クロード☆
    path('ai/chat/', views.ai_chat, name='ai_chat'),