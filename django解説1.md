# Django CBV の引数解説
## `self, request, *args, **kwargs`

---

## 結論
それぞれ役割が全然違う。

---

## 1個ずつ解説

### `self`
クラス自身。CBVのときだけ出てくる。

```python
class IndexView(CreateView):
    def form_valid(self, form):
        self.request.user  # selfでクラスの属性にアクセスできる
```

---

### `request`
**ブラウザから送られてくる全情報の塊。**

```python
request.user          # ログイン中のユーザー
request.method        # "GET" or "POST"
request.GET           # URLの ?query=xxx の部分
request.POST          # フォームで送られたデータ
request.body          # JSONデータ（ai_chatで使ってたやつ）
```

実際のコード例：
```python
body = json.loads(request.body)  # フロントからのJSON
user_message = body.get("message", "")
```

---

### `*args`
**位置引数をタプルで受け取る。**

URLのパラメータが入ってくる。

```python
# urls.py
path('event/<int:pk>/', EditEvent.as_view()),

# views.py
def get(self, request, *args, **kwargs):
    print(args)    # () ← 基本空
```

> CBVでargsを直接使うことはほぼない。**「おまじない」くらいの認識でOK。**

---

### `**kwargs`
**キーワード引数を辞書で受け取る。**

URLのパラメータが名前付きで入ってくる。

```python
# urls.py
path('event/<int:pk>/', EditEvent.as_view()),

# views.py
def get(self, request, *args, **kwargs):
    print(kwargs)  # {"pk": 5} ← これ
    pk = kwargs.get('pk')  # 取り出し方
```

---

## 図で整理

```
ブラウザ
  │
  │ GET /event/5/?query=test
  │
  ▼
def get(self, request, *args, **kwargs)
         │               │        │
         │               │        └── {"pk": 5}  ← URLの /5/
         │               └── ()  ← 基本空
         └── request.GET = {"query": "test"}  ← ?以降
```

---

## まとめ：結局どれ使うの？

| 引数 | 使用頻度 | 主な用途 |
|---|---|---|
| `self` | 毎回 | クラスの属性アクセス |
| `request` | 毎回 | ユーザー情報・送信データ |
| `*args` | ほぼ使わない | おまじない |
| `**kwargs` | たまに | URLパラメータ取得 |

`self`と`request`を完全に使いこなせれば8割解決する。
