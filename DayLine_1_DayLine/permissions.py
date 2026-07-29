"""
permissions.py : ルーム内の権限（Authority）と、その権限で何ができるかを一元管理するモジュール。

これまでは views.py のあちこちで
    member.authority.authority_code in ['admin', 'owner']
のように権限コードを直接ベタ書きしていたため、
権限を1つ増やすたびに全ビューを直す必要があった。
ここに「権限 → 許可される操作」の対応表を1か所だけ持たせて、
ビュー側は has_room_permission() を呼ぶだけにする。
"""

from django.core.exceptions import PermissionDenied

from .models import RoomMember


# --- 操作の識別子 -------------------------------------------------
# 「何をする権限か」を表す文字列。文字列直書きのtypoを防ぐために定数にしておく。
PERM_ROOM_DELETE = 'room_delete'    # ルームそのものの削除
PERM_ROOM_MANAGE = 'room_manage'    # ルーム名・説明の変更、メンバーの権限変更／追放
PERM_EVENT_CREATE = 'event_create'  # イベントの作成
PERM_EVENT_EDIT = 'event_edit'      # イベントの編集
PERM_EVENT_DELETE = 'event_delete'  # イベントの削除


# --- 権限コード ---------------------------------------------------
# Authority.authority_code に入る値。DBの中身とここを一致させる
# （実データは migrations/0007_authority_master_data.py で投入している）
AUTHORITY_OWNER = 'owner'
AUTHORITY_ADMIN = 'admin'
AUTHORITY_USER = 'user'
AUTHORITY_MEMBER = 'member'
AUTHORITY_GUEST = 'guest'

# 表示名。データマイグレーションから参照する
AUTHORITY_NAMES = {
    AUTHORITY_OWNER: 'オーナー',
    AUTHORITY_ADMIN: '管理者',
    AUTHORITY_USER: 'ユーザー',
    AUTHORITY_MEMBER: 'メンバー',
    AUTHORITY_GUEST: 'ゲスト',
}


# --- 権限 → 許可される操作の対応表 --------------------------------
# オーナー ：すべての権限を持つ
# 管理者   ：ルームの削除以外なら何でもできる
# ユーザー ：イベントのCRUDだけなら何でもできる
# メンバー ：イベントの追加だけならできる
# ゲスト   ：何もできない（イベントの閲覧のみ）
AUTHORITY_PERMISSIONS = {
    AUTHORITY_OWNER: {
        PERM_ROOM_DELETE,
        PERM_ROOM_MANAGE,
        PERM_EVENT_CREATE,
        PERM_EVENT_EDIT,
        PERM_EVENT_DELETE,
    },
    AUTHORITY_ADMIN: {
        PERM_ROOM_MANAGE,
        PERM_EVENT_CREATE,
        PERM_EVENT_EDIT,
        PERM_EVENT_DELETE,
    },
    AUTHORITY_USER: {
        PERM_EVENT_CREATE,
        PERM_EVENT_EDIT,
        PERM_EVENT_DELETE,
    },
    AUTHORITY_MEMBER: {
        PERM_EVENT_CREATE,
    },
    AUTHORITY_GUEST: set(),
}


def get_room_member(user, room):
    """
    ログインユーザーが指定ルームのメンバーなら RoomMember を返す。
    メンバーでない（＝そのルームに属していない）場合は None を返す。
    """
    if not user or not user.is_authenticated:
        return None
    # RoomMember.room は null=True なので、room が None のまま検索すると
    # ルームが外れた孤立レコードに誤ヒットして権限があると誤判定しうる。先に弾く
    if room is None:
        return None
    return RoomMember.objects.filter(room=room, user=user).select_related('authority').first()


def has_room_permission(user, room, permission):
    """
    user が room に対して permission の操作をしてよいかを判定して True / False を返す。

    user       : ログイン中のユーザー（request.user）
    room       : 対象の Room
    permission : このモジュールの PERM_* 定数
    """
    member = get_room_member(user, room)
    if member is None:
        # そもそもルームのメンバーではないので何もできない
        return False
    if member.authority is None:
        # 権限が外れているデータは安全側に倒して不許可にする
        return False
    # 未知の権限コードが入っていた場合も空集合として扱う（＝不許可）
    allowed = AUTHORITY_PERMISSIONS.get(member.authority.authority_code, set())
    return permission in allowed


def require_room_permission(user, room, permission):
    """
    has_room_permission() の例外版。
    権限がなければ PermissionDenied（403）を投げる。
    ビューの中で1行で権限チェックを書きたいときに使う。
    """
    if not has_room_permission(user, room, permission):
        raise PermissionDenied
