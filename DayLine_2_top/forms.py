from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'お名前'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': '例:example.com'
        })
    )
    subject = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'お問い合わせ内容の件名'
        })
    )
    body = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'ご質問やご要望の内容を詳しくご記入ください'
        })
    )