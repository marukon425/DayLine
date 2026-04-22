from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.http import HttpResponse
from .forms import ContactForm
from django.core.mail import EmailMessage
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView
# Create your views here.


class TopView(TemplateView):
    template_name = 'top.html'

#参考:https://qiita.com/minamoto2501/items/829ab8cd08b45b7b6d27
#コンタクト
class ContactView(FormView):
    # 使用するテンプレート(HTML)を指定
    template_name = 'contact.html'
    # ContactFormクラス(新たなクラスを作成)を活用
    form_class = ContactForm
    # 問い合わせ送信"完了後"の行き先を指定
    success_url = reverse_lazy('blogapp:contact')

    # メール送信(問い合わせ送信)のメソッド
    def form_valid(self, form):

        # HTML(フォーム)より送られたデータを各変数に格納
        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        title = form.cleaned_data['title']
        message = form.cleaned_data['message']

        #####  送信準備  #####
        # メールのタイトルを設定
        subject = 'お問い合わせ: {}'.format(title)
        # メールの本文を設定
        message = \
            '送信者名:{0}\n メールアドレス: {1}\n タイトル:{2}\n メッセージ:\n{3}' \
            .format(name, email, title, message)

        # 送信元のメールアドレスを設定
        from_email = 'asmin@example.com'
        # 宛先のメールアドレスを設定
        to_list = ['admin@example.cpm']
        # タイトル、本文、送信先、宛先をまとめる
        # EmailMessageクラスをインスタンス化して、messageオブジェクトを生成
        message = EmailMessage(subject=subject, body=message, from_email=from_email,to=to_list)
        # mwssageオブジェクトのsendメソッドの実行(メール送信)
        message.send()
        # 送信完了後のメッセージ
        messages.success(self.request, 'お問い合わせは正常に送信されました。')
        # 戻り値
        return super().form_valid(form)


#利用規約
class Terms(TemplateView):
    template_name = 'terms.html'

#プライバシーポリシー
class Privacy(TemplateView):
    template_name = 'privacy.html'
