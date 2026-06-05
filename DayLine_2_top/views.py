from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.http import HttpResponse
from .forms import ContactForm
from django.core.mail import EmailMessage
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.conf import settings
# Create your views here.


class TopView(TemplateView):
    template_name = 'top.html'

#参考:https://qiita.com/minamoto2501/items/829ab8cd08b45b7b6d27
#コンタクト
class ContactView(FormView):
    template_name = 'contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('DayLine_2_top:contact')

    def form_valid(self, form):
        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        subject_text = form.cleaned_data['subject']
        body_text = form.cleaned_data['body']

        subject = 'お問い合わせ: {}'.format(subject_text)
        body = '送信者名:{0}\n メールアドレス: {1}\n 件名:{2}\n メッセージ:\n{3}'.format(
            name, email, subject_text, body_text
        )

        mail = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['daylineofiice@gmail.com'],
            reply_to=[email],
        )
        mail.send()
        messages.success(self.request, 'お問い合わせは正常に送信されました。')
        return super().form_valid(form)


#利用規約
class Terms(TemplateView):
    template_name = 'terms.html'

#プライバシーポリシー
class Privacy(TemplateView):
    template_name = 'privacy.html'
