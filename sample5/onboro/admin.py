from distutils.command.register import register

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect

# Register your models here.
from .models import User, Category, Book, Chapter, TransactionRecord


class UserAdmin(BaseUserAdmin):
    list_display = ("username", "is_staff", "coin")
admin.site.register(User, UserAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['display_order', 'name']

admin.site.register(Category, CategoryAdmin)

class ChapterInline(admin.StackedInline):
    model = Chapter
    extra = 1

class BookAdmin(admin.ModelAdmin):
    model = Book
    list_display = ['title', 'published']
    inlines = [ChapterInline]

admin.site.register(Book, BookAdmin)

class TransactionRecordAdmin(admin.ModelAdmin):
    model = TransactionRecord
    list_display = ['kind', 'amount', 'user', 'book', 'datetime']
    list_filter = ['kind']
    search_fields = ['user__username', 'book__title']
    search_help_text = 'ユーザー名と書籍名で検索できます'

    def delete_model(self, request, obj):
        # 削除を無効化し、警告メッセージを表示
        messages.error(request, "この取引記録は削除できません。")  # エラーメッセージを使用
        return HttpResponseRedirect(reverse('admin:onboro_transactionrecord_changelist'))

    def has_delete_permission(self, request, obj=None):
        """削除権限を常に無効化する"""
        return False

admin.site.register(TransactionRecord, TransactionRecordAdmin)