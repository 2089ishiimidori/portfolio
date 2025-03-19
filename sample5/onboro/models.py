from django.db import models
from django.contrib.auth.models import AbstractUser
import logging
from django.db import transaction

logger = logging.getLogger(__name__)


class User(AbstractUser):
    coin = models.PositiveIntegerField(default=0, verbose_name='コイン残高')

    books = models.ManyToManyField(
        # まだ定義してないので文字列で指定する必要がある
        'book',
        through='TransactionRecord'
    )

    # @property
    # def current_coin(self):
    #     # 最新の取引記録を取得
    #     transactions = TransactionRecord.objects.filter(user=self).order_by('-datetime')
    #
    #     # 初期コイン残高を設定
    #     current_balance = self.coin
    #
    #     # 取引記録が存在する場合は、各取引を反映
    #     for transaction in transactions:
    #         if transaction.kind == TransactionRecord.Kind.CHARGE:
    #             current_balance += transaction.amount
    #         elif transaction.kind == TransactionRecord.Kind.USE:
    #             current_balance -= transaction.amount
    #         elif transaction.kind == TransactionRecord.Kind.CHANGE_PLUS:
    #             current_balance += transaction.amount
    #         elif transaction.kind == TransactionRecord.Kind.CHANGE_MINUS:
    #             current_balance -= transaction.amount
    #
    #     return current_balance  # 計算されたコイン残高を返す

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    custom_setting = models.CharField(max_length=20, default='normal')  # 文字の大きさ
    background_color = models.CharField(max_length=10, choices=[('white', '白'), ('black', '黒')], default='white')  # 背景色
    icon = models.ImageField(upload_to='icons/', blank=True, null=True)  # アイコン

    def __str__(self):
        return self.user.username

class Category(models.Model):
    display_order = models.IntegerField(verbose_name='表示順')
    name = models.CharField(max_length=80, verbose_name='名前')

    class Meta:
        ordering = ['display_order']

        verbose_name = 'カテゴリ'
        verbose_name_plural = 'カテゴリ'

    def __str__(self):
        return self.name

class ImageUpload(models.Model):
    image = models.ImageField(upload_to='images/')
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.description if self.description else 'Image {}'.format(self.pk)

class Book(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='カテゴリ')
    title = models.CharField(max_length=80, verbose_name='タイトル')
    # 画像をアップロードする機能実装
    image = models.ImageField(upload_to='images/', default='default_image_path.jpg', verbose_name='画像')  # デフォルトの画像パスを指定
    abstract = models.TextField(verbose_name='概要')
    price = models.PositiveIntegerField(verbose_name='価格')
    published = models.BooleanField('公開')

    class Meta:
        verbose_name = '書籍'
        verbose_name_plural = '書籍'

    def __str__(self):
        return self.title

class Chapter(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name='書籍')
    number = models.PositiveIntegerField(verbose_name='章番号')
    title = models.CharField(max_length=80, verbose_name='章名')
    body = models.TextField(verbose_name='本文')

    class Meta:
        ordering = ['number']

        verbose_name = '章'
        verbose_name_plural = '章'

    def __str__(self):
        return self.title

    def title_with_number(self):
        return f'第{self.number}章{self.title}'

    def next_chapter(self):
        return self.book.chapter_set.filter(number=self.number+1).first()

    def prev_chapter(self):
        return self.book.chapter_set.filter(number=self.number-1).first()


class TransactionRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='ユーザー')
    book = models.ForeignKey(Book, null=True, blank=True, on_delete=models.PROTECT, verbose_name='書籍')
    datetime = models.DateTimeField(verbose_name='日時')

    class Kind(models.TextChoices):
        CHARGE = 'CHARGE', 'チャージ'  # 表示名を「チャージ」に変更
        USE = 'USE', '使用'  # 表示名を「使用」に変更
        CHANGE_PLUS = 'CHANGE_PLUS', '修正補填' #削除ボタンを消すため追加、coinをプラス
        CHANGE_MINUS = 'CHANGE_MINUS', '修正除去' #削除ボタンを消すため追加、coinをマイナス

    kind = models.CharField(max_length=20, choices=Kind.choices, verbose_name='取引種別')
    amount = models.PositiveIntegerField(verbose_name='金額')

    class Meta:
        verbose_name = '取引記録'
        verbose_name_plural = '取引記録'

    def delete(self, *args, **kwargs):
        raise Exception("この取引記録は削除できません。")

    def save(self, *args, **kwargs):
        with transaction.atomic():
            is_new = self.pk is None  # 新規作成かどうかを判定
            original_kind = None

            if not is_new:
                original = TransactionRecord.objects.get(pk=self.pk)
                original_kind = original.kind

            super().save(*args, **kwargs)  # 通常の保存処理

            if is_new:
                if self.kind == self.Kind.CHARGE:
                    self.user.coin += self.amount
                elif self.kind == self.Kind.USE:
                    self.user.coin -= self.amount
                elif self.kind == self.Kind.CHANGE_PLUS:
                    self.user.coin += self.amount
                elif self.kind == self.Kind.CHANGE_MINUS:
                    self.user.coin -= self.amount
            else:
                if original_kind == self.Kind.CHARGE:
                    self.user.coin -= original.amount
                elif original_kind == self.Kind.USE:
                    self.user.coin += original.amount
                elif original_kind == self.Kind.CHANGE_PLUS:
                    self.user.coin -= original.amount
                elif original_kind == self.Kind.CHANGE_MINUS:
                    self.user.coin += original.amount

            self.user.save()  # 最後にユーザーのデータを保存

# class TransactionRecord(models.Model):
#     user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='ユーザー')
#     book = models.ForeignKey(Book, null=True, blank=True, on_delete=models.PROTECT, verbose_name='書籍')
#     datetime = models.DateTimeField(verbose_name='日時')
#
#     class Kind(models.TextChoices):
#         CHARGE = 'CHARGE', 'チャージ'  # 表示名を「チャージ」に変更
#         USE = 'USE', '使用'  # 表示名を「使用」に変更
#         CHANGE_PLUS = 'CHANGE_PLUS', '修正補填'  # coinをプラス
#         CHANGE_MINUS = 'CHANGE_MINUS', '修正除去'  # coinをマイナス
#
#     kind = models.CharField(max_length=20, choices=Kind.choices, verbose_name='取引種別')
#     amount = models.PositiveIntegerField(verbose_name='金額')
#
#     class Meta:
#         verbose_name = '取引記録'
#         verbose_name_plural = '取引記録'
#
#     def delete(self, *args, **kwargs):
#         raise Exception("この取引記録は削除できません。")
#
#     def save(self, *args, **kwargs):
#         with transaction.atomic():
#             is_new = self.pk is None  # 新規作成かどうかを判定
#             original_kind = None
#             original_amount = 0
#
#             if not is_new:
#                 original = TransactionRecord.objects.get(pk=self.pk)
#                 original_kind = original.kind
#                 original_amount = original.amount
#
#             # 通常の保存処理
#             super().save(*args, **kwargs)
#
#             # コインの状態を更新
#             if is_new:
#                 # 新規作成時のコインの加算・減算処理
#                 if self.kind == self.Kind.CHARGE:
#                     self.user.coin += self.amount
#                 elif self.kind == self.Kind.USE:
#                     self.user.coin -= self.amount
#                 elif self.kind == self.Kind.CHANGE_PLUS:
#                     self.user.coin += self.amount
#                 elif self.kind == self.Kind.CHANGE_MINUS:
#                     self.user.coin -= self.amount
#             else:
#                 # 更新時のコインの加算・減算処理
#                 if original_kind == self.Kind.CHARGE:
#                     self.user.coin -= original_amount
#                 elif original_kind == self.Kind.USE:
#                     self.user.coin += original_amount
#                 elif original_kind == self.Kind.CHANGE_PLUS:
#                     self.user.coin -= original_amount
#                 elif original_kind == self.Kind.CHANGE_MINUS:
#                     self.user.coin += original_amount
#
#                 # 新しい取引の種類に基づいてコインを更新
#                 if self.kind == self.Kind.CHARGE:
#                     self.user.coin += self.amount
#                 elif self.kind == self.Kind.USE:
#                     self.user.coin -= self.amount
#                 elif self.kind == self.Kind.CHANGE_PLUS:
#                     self.user.coin += self.amount
#                 elif self.kind == self.Kind.CHANGE_MINUS:
#                     self.user.coin -= self.amount
#
#             # 最後にユーザーのデータを保存
#             self.user.save()