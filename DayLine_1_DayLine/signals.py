# signals.py : モデルが保存、更新、削除されたときにsignalで検知して必要な処理をする

# 
from django.db.models.signals import post_save # post_save: モデルが保存された後に発火するシグナル(検知)
from django.dispatch import receiver # デコレーター(この関数はシグナルを使いますよって宣言するためのもの)

# 使うモデルをインポート
from DayLine_3_accounts.models import CustomUser
from .models import *

# アカウント作成と同時に自分専用のルームを作る
@receiver(post_save, sender=CustomUser)#カスタムユーザーが保存されたら発火する(サインアップのとき)
def create_room_for_user(sender, instance, created, **kwargs):
    '''
    create_room_for_userはdjangoが自動で呼ぶ
    sender:どのモデルが送信されたか
    instance:実際に保存されたオブジェクト
    created:新規作成かどうか
    **kwargs:その他の情報
    '''
    # ユーザーが作成されたら(新規作成)
    if created:

        # 個人用ルーム作成
        room = Room.objects.create(
            room_name="My Calendar",
            owner=instance,
            is_personal=True
        )

        authority, _ = Authority.objects.get_or_create(
            authority_code="admin",
            defaults={
                "authority_name": "オーナー"
            }
        )

        RoomMember.objects.create(
            room=room,
            user=instance,
            authority=authority
        )



from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=Event)
def notify_event_created(sender, instance, created, **kwargs):
    if created:
        # instanceはEventオブジェクト!!

        recipient_list = []
        #ここにfor文でルームに所属してるメンバーのメルアドをrecipient_listに入れていく※イベントを登録した本人のメルアドは除外する
        members = instance.room.roommember_set.all()
        for member in members:
            recipient_list.append(member.user.email)
            #試験的に機能はオフにする
            # if not member == instance.created_by.username:
            #     recipient_list.append(member.user.username)
            # ただしイベント作成者は除外する
        subject = "イベントが作成されました"
        message = f"""
        {instance.room.room_name}の{instance.created_by.username}が{instance.title}を追加しました。\n
        開始日：{instance.start_date}
        """
        from_email = settings.EMAIL_HOST_USER
        send_mail(subject, message, from_email, recipient_list)
