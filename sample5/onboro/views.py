from lib2to3.fixes.fix_input import context
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.defaultfilters import title
from django.views import generic
from django.contrib.auth import views as auth_views
from django.contrib.auth import mixins as auth_mixins
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import BookImageUploadForm  # アップロード用のフォームをインポート
from .forms import TransactionRecordForm  # 取引記録フォームを作成する必要があります
from django.core.exceptions import PermissionDenied # 取引記録を削除させなくする
from django.contrib.auth.decorators import login_required
from .forms import CustomSettingForm, IconUploadForm

import csv
import codecs

from unicodedata import category

from .models import User, Book, TransactionRecord
from .forms import UserImportForm, BookSearchForm, CoinChargeForm, CoinUseForm

import logging

logger = logging.getLogger(__name__)


class BookSearchMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #フォームの初期値として「送信された検索条件」を設定
        context['search_form'] = BookSearchForm(self.request.GET)
        return context


class HomeView(BookSearchMixin, generic.TemplateView):
    template_name = 'onboro/home.html'


class LoginView(auth_views.LoginView):
    template_name = 'onboro/login.html'


class LogoutView(auth_views.LogoutView):
    pass


def staff_required(user):
    return user.is_staff


class StaffRequiredMixin(auth_mixins.UserPassesTestMixin):
    def test_func(self):
        return staff_required(self.request.user)


class UserIndexView(StaffRequiredMixin, generic.ListView):
    queryset = User.objects.filter(is_staff=False)
    template_name = 'onboro/user_index.html'
    context_object_name = 'users'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['import_form'] = UserImportForm()
        return context


class UserDetailView(StaffRequiredMixin, generic.DetailView):
    pass
    queryset = User.objects.filter(is_staff=False)
    template_name = 'onboro/user_detail.html'
    # userという名前はdjango.contrib.authにより設定されるので使えない
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['charge_form'] = CoinChargeForm(initial={'user': self.kwargs['pk']})
        return context

@login_required
def my_page_settings(request):
    user_profile = request.user.userprofile  # ユーザーのプロファイル情報を取得

    if request.method == 'POST':
        form = CustomSettingForm(request.POST, instance=user_profile)
        icon_form = IconUploadForm(request.POST, request.FILES, instance=user_profile)

        if 'update_settings' in request.POST and form.is_valid():
            form.save()
            messages.success(request, 'カスタム設定を更新しました。')
            return redirect('onboro:my_page_settings')  # リダイレクトするURLを指定

        elif 'upload_icon' in request.POST and icon_form.is_valid():
            icon_form.save()
            messages.success(request, 'アイコンをアップロードしました。')
            return redirect('onboro:my_page_settings')  # リダイレクトするURLを指定

    else:
        form = CustomSettingForm(instance=user_profile)
        icon_form = IconUploadForm(instance=user_profile)

    context = {
        'form': form,
        'icon_form': icon_form,
        'user': request.user,
    }
    return render(request, 'onboro/my_page_settings.html', context)

# 関数として定義しておいた「スタッフ権限が必要」を使い、一般ユーザーはアクセスできないようにする
@user_passes_test(staff_required)
def user_import(request):
    if request.method == 'POST':
        # 「ファイル内容」以外はPOSTに格納されるので両方を指定する
        form = UserImportForm(request.POST, request.FILES)
        if form.is_valid():
            # validation実行後はclean_dateに内容が設定される
            file = form.cleaned_data['file']
            # fileはバイナリオープンされるのでcsvで読み込むにはdecodeが必要
            reader = csv.DictReader(codecs.iterdecode(file, 'utf-8'))

            try:
                # トランザクションとして実行（一つでもエラーになる場合は全部の追加を取りやめる）
                # with文を使い、その内部に「処理」を書く
                with transaction.atomic():
                    for row in reader:
                        # is_activeはint経由でboolに変換
                        row['is_active'] = bool(int(row['is_active']))
                        # Userはパスワードについて特別処理が必要なため、専用のcreate_userメソッドが用意されている
                        # usernameは一意である必要があるため、同じusernameがあるとIntegrityError（例外）が発生する
                        User.objects.create_user(**row)
                    messages.success(request, 'インポートに成功しました。')
            except IntegrityError:
                messages.error(request, 'インポートが行えませんでした。ユーザー名が重複している可能性があります。')

    return redirect('onboro:user_index')


class BookSearchView(BookSearchMixin, generic.ListView):
    template_name = 'onboro/book_search.html'
    context_object_name = 'books'

    def get_queryset(self):
        # BookSerchFormは使わず、直接取得する方がわかりやすい
        category = self.request.GET['category']
        word = self.request.GET['word']

        # 公開しているもののみ対象とする
        books = Book.objects.filter(published=True)
        # カテゴリが認定されていれば条件に加える
        if category:
            books = books.filter(category__pk=category)
        # 検索ワードが指定されていれば条件に加える
        # タイトルと概要は「どちらかに書いてあれば(or)」でカテゴリとはANDになる
        if word:
            q1 = Q(title__contains=word)
            q2 = Q(abstract__contains=word)
            books = books.filter(q1 | q2)

        return books


# 検索結果画面でリンクを設定するので詳細ビューも定義します
# テンプレートは第3項で作成します

def can_view_chapter(user, book_id):
    if user.is_authenticated:
        if user.is_staff:
            return True
        if user.books.filter(pk=book_id).exists():
            return True

    return False


class BookDetailView(BookSearchMixin, generic.DetailView):
    queryset = Book.objects.filter(published=True)
    template_name = 'onboro/book_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ユーザーが書籍を購入していなければ購入フォームを用意する
        user = self.request.user
        book_pk = self.kwargs['pk']
        if user.is_authenticated:
            if not user.books.filter(pk=book_pk).exists():
                context['use_form'] = CoinUseForm(initial={
                    'user': user.pk,
                    'book': book_pk
                })

        context['can_view_chapter'] = can_view_chapter(user, book_pk)

        return context

# 書籍画像アップロード用
class BookImageUploadView(LoginRequiredMixin, generic.FormView):
    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        form = BookImageUploadForm()
        return render(request, 'onboro/upload_image.html', {'form': form, 'book': book})

class BookChapterView(BookSearchMixin, generic.DetailView):
    template_name = 'onboro/book_chapter.html'

    def get(self, request, *args, **kwargs):
        # 購入していない書籍の章に直にアクセスされたら403を返す
        book_id = self.kwargs['book_id']
        if not can_view_chapter(self.request.user, book_id):
            return HttpResponseForbidden()

        return super().get(request, args, kwargs)

    # 指定bookの中の指定chapterなのでget_objectを定義する必要あり
    def get_object(self, queryset=None):
        book_id = self.kwargs['book_id']
        number = self.kwargs['number']
        # 非公開のbookにはアクセスできないようにする
        book = get_object_or_404(Book, pk=book_id, published=True)
        # 存在しない章にアクセスされたとき対策としてこちらもget_or_404を使う
        # get_or_404にはManagerを渡せる
        chapter = get_object_or_404(book.chapter_set, number=number)
        return chapter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # get_objectでchapter返すのでchapterが設定される
        chapter = context['chapter']
        # chapterの親もcontextにあった方がいいので設定
        context['book'] = chapter.book
        return context

@user_passes_test(staff_required)
def transaction_charge(request, pk):
    if request.method == 'POST':
        form = CoinChargeForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            # 予想外のことがない限り例外は発生しないのでtry-exceptはしない
            with transaction.atomic():
                user = record.user
                user.coin += record.amount
                user.save()

                record.kind = TransactionRecord.Kind.CHARGE.value
                record.datetime = timezone.now()
                record.save()

    return redirect('onboro:user_detail', pk)

def transaction_use(request, pk):
    # リダイレクト先がbook_detailなのでGETされるのは想定外（Django的にエラーにする）
    if request.method == 'POST':
        form = CoinUseForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            user = record.user
            book = record.book

            if user.coin < book.price:
                messages.warning(request, 'コインが足りません。')
                # コード重複にはなるがインデントが深くなるとわかりにくくなるのでここでreturn
                return redirect('onboro:book_detail', book.pk)

            with transaction.atomic():
                user.coin -= book.price
                user.save()

                record.kind = TransactionRecord.Kind.USE.value
                record.amount = book.price
                record.datetime = timezone.now()
                record.save()

            return redirect('onboro:book_detail', book.pk)

def delete_transaction(request, transaction_id):
    # 削除を許可しない
    raise PermissionDenied("削除は許可されていません。")

def edit_transaction(request, transaction_id):
    transaction = get_object_or_404(TransactionRecord, pk=transaction_id)

    if request.method == 'POST':
        form = TransactionRecordForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            return redirect('transaction_list')  # 取引記録の一覧ページにリダイレクト
    else:
        form = TransactionRecordForm(instance=transaction)

    return render(request, 'edit_transaction.html', {'form': form})

def transaction_and_coins_view(request):
    user = request.user
    transaction_records = TransactionRecord.objects.filter(user=user)  # ユーザーの取引記録を取得
    user_coins = user.coins  # ユーザーが保有しているコインの情報を取得（フィールド名に応じて変更）

    context = {
        'transaction_records': transaction_records,
        'user_coins': user_coins,
    }
    return render(request, 'onboro:transaction_records.html', context)
#
