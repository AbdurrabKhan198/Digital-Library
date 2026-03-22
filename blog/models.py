from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from ckeditor_uploader.fields import RichTextUploadingField
from library.models import Scholar

def scholar_cover_upload(instance, filename):
    """Path: scholars/{domain}/{scholar}/cover.jpg"""
    domain = slugify(instance.knowledge_domain) if instance.knowledge_domain else "unknown-domain"
    scholar = instance.scholar.slug if (instance.scholar and instance.scholar.slug) else "unknown-scholar"
    ext = filename.split('.')[-1]
    return f"scholars/{domain}/{scholar}/cover.{ext}"


class ScholarArticle(models.Model):
    KNOWLEDGE_DOMAIN_CHOICES = [
        ('Religious Knowledge', 'Religious Knowledge'),
        ('Islamic Sciences', 'Islamic Sciences'),
    ]
    
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    scholar = models.ForeignKey(
        Scholar, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='blog_articles'
    )
    knowledge_domain = models.CharField(
        max_length=50, 
        choices=KNOWLEDGE_DOMAIN_CHOICES,
        default='Religious Knowledge'
    )
    cover_image = models.ImageField(upload_to=scholar_cover_upload)
    short_description = models.TextField(
        max_length=500,
        help_text="A brief summary for the listing page."
    )
    content = RichTextUploadingField()
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='blog_articles'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Scholar Biography"
        verbose_name_plural = "Scholar Biographies"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def increment_views(self):
        """Increment view count atomically."""
        ScholarArticle.objects.filter(pk=self.pk).update(views=models.F("views") + 1)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:article_detail', kwargs={'slug': self.slug})


class ScholarArticleComment(models.Model):
    article = models.ForeignKey(
        ScholarArticle, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self):
        return f"Comment by {self.user.username} on {self.article.title}"
