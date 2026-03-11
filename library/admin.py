"""
Admin configuration for the Islamic Digital Library.

Provides moderation capabilities for books (approve/reject/delete),
bookmark management, and a library analytics dashboard.
"""

from django.contrib import admin
from django.db.models import Sum, Count
from django.template.response import TemplateResponse
from django.urls import path
from django.contrib.auth.models import User
from .models import (
    Book, Category, Scholar, Language, KnowledgeDomain,
    BookBookmark, LibraryFeedback, IssueReport
)


@admin.register(KnowledgeDomain)
class KnowledgeDomainAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "category_count")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("order",)

    def category_count(self, obj):
        return obj.categories.count()
    category_count.short_description = "Categories"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "knowledge_domain", "slug", "order", "approved_book_count")
    list_filter = ("knowledge_domain",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("order", "name")


@admin.register(Scholar)
class ScholarAdmin(admin.ModelAdmin):
    list_display = ("name", "field_of_expertise", "birth_year", "death_year")
    list_filter = ("field_of_expertise",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "field_of_expertise")


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "title", "knowledge_domain", "scholar", "category", "language",
        "status", "is_featured", "uploaded_by", "views", "downloads", "created_at"
    )
    list_filter = ("status", "is_featured", "knowledge_domain", "category", "language", "created_at")
    search_fields = ("title", "scholar__name", "description")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("views", "downloads", "created_at", "updated_at", "uploaded_by")
    list_editable = ("status", "is_featured")
    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        ("Book Information", {
            "fields": (
                "title", "slug", "knowledge_domain",
                "scholar", "category", "language", "description"
            )
        }),
        ("Files", {
            "fields": ("pdf_file", "cover_image")
        }),
        ("Moderation", {
            "fields": ("status", "is_featured", "uploaded_by")
        }),
        ("Statistics", {
            "fields": ("views", "downloads"),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    actions = ["approve_books", "reject_books", "mark_featured", "unmark_featured"]

    @admin.action(description="Approve selected books")
    def approve_books(self, request, queryset):
        updated = queryset.update(status="approved")
        self.message_user(request, f"{updated} book(s) approved successfully.")

    @admin.action(description="Reject selected books")
    def reject_books(self, request, queryset):
        updated = queryset.update(status="rejected")
        self.message_user(request, f"{updated} book(s) rejected.")

    @admin.action(description="⭐ Mark as Featured")
    def mark_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"{updated} book(s) marked as featured.")

    @admin.action(description="Remove Featured status")
    def unmark_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f"{updated} book(s) removed from featured.")


@admin.register(BookBookmark)
class BookBookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "book", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "book__title")
    readonly_fields = ("user", "book", "created_at")
    date_hierarchy = "created_at"
    list_per_page = 30

    def has_add_permission(self, request):
        return False


# =========================================================================
# COMMUNITY FEEDBACK ADMIN
# =========================================================================

@admin.register(LibraryFeedback)
class LibraryFeedbackAdmin(admin.ModelAdmin):
    list_display = ("get_sender", "email", "short_message", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "email", "message", "user__username")
    readonly_fields = ("user", "name", "email", "message", "created_at")
    date_hierarchy = "created_at"
    list_per_page = 30

    def get_sender(self, obj):
        if obj.user:
            return f"{obj.user.username} (registered)"
        return obj.name or "Anonymous"
    get_sender.short_description = "Submitted By"

    def short_message(self, obj):
        return obj.message[:80] + "..." if len(obj.message) > 80 else obj.message
    short_message.short_description = "Message"

    def has_add_permission(self, request):
        return False  # Feedback is user-submitted only


@admin.register(IssueReport)
class IssueReportAdmin(admin.ModelAdmin):
    list_display = (
        "get_sender", "issue_type", "related_book",
        "status", "short_message", "created_at"
    )
    list_filter = ("issue_type", "status", "created_at")
    search_fields = ("name", "email", "message", "user__username", "related_book__title")
    readonly_fields = ("user", "name", "email", "issue_type", "message", "related_book", "created_at")
    list_editable = ("status",)
    date_hierarchy = "created_at"
    list_per_page = 30

    fieldsets = (
        ("Reporter", {
            "fields": ("user", "name", "email")
        }),
        ("Issue Details", {
            "fields": ("issue_type", "related_book", "message")
        }),
        ("Status", {
            "fields": ("status",)
        }),
        ("Metadata", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    actions = ["mark_resolved", "mark_in_progress", "dismiss_reports"]

    def get_sender(self, obj):
        if obj.user:
            return f"{obj.user.username} (registered)"
        return obj.name or "Anonymous"
    get_sender.short_description = "Submitted By"

    def short_message(self, obj):
        return obj.message[:60] + "..." if len(obj.message) > 60 else obj.message
    short_message.short_description = "Message"

    @admin.action(description="Mark selected as Resolved")
    def mark_resolved(self, request, queryset):
        updated = queryset.update(status="resolved")
        self.message_user(request, f"{updated} issue(s) marked as resolved.")

    @admin.action(description="Mark selected as In Progress")
    def mark_in_progress(self, request, queryset):
        updated = queryset.update(status="in_progress")
        self.message_user(request, f"{updated} issue(s) marked as in progress.")

    @admin.action(description="Dismiss selected reports")
    def dismiss_reports(self, request, queryset):
        updated = queryset.update(status="dismissed")
        self.message_user(request, f"{updated} report(s) dismissed.")

    def has_add_permission(self, request):
        return False  # Reports are user-submitted only


# =========================================================================
# ADMIN ANALYTICS DASHBOARD
# =========================================================================

class LibraryAdminSite(admin.AdminSite):
    """
    Extended admin site with a library analytics dashboard.
    """

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("library-analytics/", self.admin_view(self.analytics_view), name="library_analytics"),
        ]
        return custom_urls + urls

    def analytics_view(self, request):
        """Render the library analytics dashboard."""
        approved_books = Book.objects.filter(status="approved")

        context = {
            **self.each_context(request),
            "title": "Library Analytics",
            # Totals
            "total_books": Book.objects.count(),
            "approved_books": approved_books.count(),
            "pending_books": Book.objects.filter(status="pending").count(),
            "total_scholars": Scholar.objects.count(),
            "total_categories": Category.objects.count(),
            "total_users": User.objects.count(),
            "total_bookmarks": BookBookmark.objects.count(),
            "total_feedback": LibraryFeedback.objects.count(),
            "total_issues": IssueReport.objects.filter(status="open").count(),
            # Top lists
            "most_downloaded": approved_books.order_by("-downloads")[:10],
            "most_viewed": approved_books.order_by("-views")[:10],
            "top_categories": (
                Category.objects.annotate(
                    book_count=Count("books", filter=Q(books__status="approved"))
                ).order_by("-book_count")[:10]
            ),
            "top_scholars": (
                Scholar.objects.annotate(
                    book_count=Count("books", filter=Q(books__status="approved"))
                ).order_by("-book_count")[:10]
            ),
            "recent_uploads": Book.objects.order_by("-created_at")[:10],
        }
        return TemplateResponse(request, "admin/library_analytics.html", context)


# Override the default admin site
admin.site.__class__ = LibraryAdminSite
