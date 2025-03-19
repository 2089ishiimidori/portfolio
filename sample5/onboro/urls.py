from django.urls import path
from setuptools.extern import names
from django.conf import settings
from django.conf.urls.static import static
from .views import edit_transaction
from .views import my_page_settings

from . import views

app_name = 'onboro'
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('login', views.LoginView.as_view(), name='login'),
    path('logout', views.LogoutView.as_view(), name='logout'),

    path('users',views.UserIndexView.as_view(), name='user_index'),
    path('users/<int:pk>', views.UserDetailView.as_view(), name='user_detail'),
    path('my_page/settings/', views.my_page_settings, name='my_page_settings'),
    path('users/import', views.user_import, name='user_import'),

    path('search', views.BookSearchView.as_view(), name='book_search'),
    path('books/<int:pk>', views.BookDetailView.as_view(), name='book_detail'),
    path('books/<int:book_id>/chapters/<int:number>', views.BookChapterView.as_view(), name='book_chapter'),

    path('users/<int:pk>/transactions/charge', views.transaction_charge, name='transaction_charge'),
    path('users/<int:pk>/transactions/use', views.transaction_use, name='transaction_use'),

    path('transaction/edit/<int:transaction_id>/', edit_transaction, name='edit_transaction'), # 取引記録

# 画像のアップロード用URL追加
    path('books/<int:pk>/upload_image/', views.BookImageUploadView.as_view(), name='upload_image'),  # 書籍の画像アップロード
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # その他のURLパターン
