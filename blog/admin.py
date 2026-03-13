from django.contrib import admin
from .models import ScholarArticle, ScholarArticleComment

@admin.register(ScholarArticle)
class ScholarArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'scholar', 'knowledge_domain', 'author', 'is_published', 'created_at')
    list_filter = ('is_published', 'knowledge_domain', 'created_at')
    search_fields = ('title', 'short_description', 'content', 'scholar__name')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'

@admin.register(ScholarArticleComment)
class ScholarArticleCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('comment_text', 'user__username', 'article__title')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "Mark selected comments as approved"
