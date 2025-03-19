from django import forms

from .models import Category, TransactionRecord, UserProfile


class UserImportForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(attrs={'accept': 'text/csv'})
    )

class CustomSettingForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['custom_setting', 'background_color', 'icon']
        widgets = {
            'custom_setting': forms.Select(choices=[
                ('small', '小さな文字'),
                ('normal', '普通の文字'),
                ('large', '大きな文字'),
            ])}

class IconUploadForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['icon']  # アイコン画像のフィールド

class BookSearchForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
    word = forms.CharField(required=False, widget=forms.TextInput(attrs={'type':'search'}))

# 書籍画像アップロード用
class BookImageUploadForm(forms.Form):
    image = forms.ImageField(label='画像')

class CoinChargeForm(forms.ModelForm):
    class Meta:
        model = TransactionRecord
        fields = ['amount', 'user']
        widgets = {
            'user': forms.HiddenInput
        }

class CoinUseForm(forms.ModelForm):
    class Meta:
        model = TransactionRecord
        fields = {'user', 'book'}
        widgets = {
            'user': forms.HiddenInput,
            'book': forms.HiddenInput
        }

class TransactionRecordForm(forms.ModelForm):
    class Meta:
        model = TransactionRecord
        fields = ['kind', 'amount', 'book']  # 編集可能なフィールドを指定