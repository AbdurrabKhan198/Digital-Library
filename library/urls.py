"""
URL configuration for the library app.

Clean URL structure with slug-based book pages.
"""

from django.urls import path
from . import views

app_name = "library"

urlpatterns = [
    # Homepage
    path("", views.HomePageView.as_view(), name="home"),

    # Book URLs
    path("books/", views.BookListView.as_view(), name="book_list"),
    path("book/<slug:slug>/", views.BookDetailView.as_view(), name="book_detail"),
    path("book/<slug:slug>/download/", views.download_book, name="book_download"),
    path("book/<slug:slug>/read/", views.ReadOnlineView.as_view(), name="book_read"),
    path("book/<slug:slug>/preview/", views.PreviewBookView.as_view(), name="book_preview"),

    # Bookmarks
    path("book/<slug:slug>/bookmark/", views.ToggleBookmarkView.as_view(), name="toggle_bookmark"),
    path("my-library/", views.MyLibraryView.as_view(), name="my_library"),

    # Upload
    path("upload/", views.BookUploadView.as_view(), name="book_upload"),
    path("upload/success/", views.UploadSuccessView.as_view(), name="upload_success"),
    path("upload-guidelines/", views.UploadGuidelinesView.as_view(), name="upload_guidelines"),

    # Categories
    path("category/<slug:slug>/", views.CategoryDetailView.as_view(), name="category_detail"),

    # Scholars
    path("scholar/<slug:slug>/", views.ScholarDetailView.as_view(), name="scholar_detail"),

    # Search
    path("search/", views.SearchView.as_view(), name="search"),

    # Community Feedback
    path("feedback/", views.FeedbackView.as_view(), name="feedback"),
    path("report-issue/", views.ReportIssueView.as_view(), name="report_issue"),

    # AJAX
    path("api/check-duplicate/", views.check_duplicate_ajax, name="check_duplicate"),
    path("api/categories-by-domain/", views.get_categories_by_domain, name="categories_by_domain"),
]
