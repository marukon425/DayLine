"""
権限（Authority）マスタを5種類に整理するマイグレーション。

やっていること:
1. 権限コードの表記ゆれを正規化する（例: "memmber" → "member"）
   重複した権限レコードがあれば RoomMember の参照をまとめてから余りを削除する。
2. owner / admin / user / member / guest の5レコードが必ず存在する状態にする。
3. ルームの作成者（Room.owner）に owner 権限を割り当て直す。
   signals.py が個人ルーム作成時に誤って "admin" を割り当てていた分の是正。
4. 最後に authority_code へ unique 制約を付けて、以後の重複登録を防ぐ。

権限ごとに何ができるかは DayLine_1_DayLine/permissions.py 側で定義している。
"""

from django.db import migrations, models


# 正規の権限コードと表示名
CANONICAL_AUTHORITIES = [
    ('owner', 'オーナー'),
    ('admin', '管理者'),
    ('user', 'ユーザー'),
    ('member', 'メンバー'),
    ('guest', 'ゲスト'),
]

# 過去に使われていた表記ゆれ → 正規コードの対応
CODE_ALIASES = {
    'memmber': 'member',
    'menber': 'member',
    'users': 'user',
    'admins': 'admin',
    'owners': 'owner',
}


def normalize_authorities(apps, schema_editor):
    Authority = apps.get_model('DayLine_1_DayLine', 'Authority')
    RoomMember = apps.get_model('DayLine_1_DayLine', 'RoomMember')
    Room = apps.get_model('DayLine_1_DayLine', 'Room')

    # --- 1. 表記ゆれを正規コードに寄せる ---
    for authority in Authority.objects.all():
        canonical_code = CODE_ALIASES.get(authority.authority_code)
        if canonical_code:
            authority.authority_code = canonical_code
            authority.save()

    # --- 2. 正規コードごとに1レコードへまとめる ---
    canonical_by_code = {}
    for code, name in CANONICAL_AUTHORITIES:
        rows = list(Authority.objects.filter(authority_code=code).order_by('pk'))
        if rows:
            keeper = rows[0]
            # 同じコードのレコードが複数あったら、参照を1本目に寄せてから残りを削除する
            for duplicate in rows[1:]:
                RoomMember.objects.filter(authority=duplicate).update(authority=keeper)
                duplicate.delete()
            keeper.authority_name = name
            keeper.save()
        else:
            keeper = Authority.objects.create(authority_code=code, authority_name=name)
        canonical_by_code[code] = keeper

    # --- 3. 想定外のコードが残っていたらゲスト扱いに寄せる ---
    #     （権限表に載っていないコードは permissions.py 側で「何もできない」判定になるため、
    #       データとしても明示的にゲストへ倒しておく）
    guest = canonical_by_code['guest']
    known_codes = [code for code, _ in CANONICAL_AUTHORITIES]
    for stray in Authority.objects.exclude(authority_code__in=known_codes):
        RoomMember.objects.filter(authority=stray).update(authority=guest)
        stray.delete()

    # --- 4. ルーム作成者には owner 権限を持たせる ---
    owner = canonical_by_code['owner']
    for room in Room.objects.exclude(owner__isnull=True):
        RoomMember.objects.filter(room=room, user=room.owner).update(authority=owner)


def noop_reverse(apps, schema_editor):
    """データの整理なので巻き戻しは何もしない（unique制約の解除だけ行われる）。"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('DayLine_1_DayLine', '0006_alter_room_room_img'),
    ]

    operations = [
        # データを整えてから unique 制約を付ける（順番が逆だと重複で失敗する）
        migrations.RunPython(normalize_authorities, noop_reverse),
        migrations.AlterModelOptions(
            name='authority',
            options={'verbose_name': '権限セット', 'verbose_name_plural': '権限セット'},
        ),
        migrations.AlterField(
            model_name='authority',
            name='authority_code',
            field=models.CharField(max_length=20, unique=True, verbose_name='権限'),
        ),
    ]
