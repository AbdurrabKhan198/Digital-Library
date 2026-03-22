"""
Models for the Islamic Digital Library.

Contains: KnowledgeDomain, Category, Scholar, Language, Book,
          BookBookmark, LibraryFeedback, IssueReport
"""

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify

from .validators import validate_pdf_file, validate_file_size


class KnowledgeDomain(models.Model):
    """
    Top-level knowledge domain.
    Examples: Religious Knowledge, Islamic Sciences
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Emoji or icon identifier"
    )
    order = models.PositiveIntegerField(default=0, help_text="Display order")

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("library:book_list") + f"?domain={self.slug}"


class Category(models.Model):
    """
    Knowledge categories belonging to a domain.
    Religious: Qur'an, Hadith, Fiqh, etc.
    Islamic Sciences: Astronomy, Mathematics, Medicine, etc.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    knowledge_domain = models.ForeignKey(
        KnowledgeDomain,
        on_delete=models.CASCADE,
        related_name="categories",
        null=True,
        blank=True,
        help_text="Which knowledge domain this category belongs to"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Heroicon name for category display"
    )
    order = models.PositiveIntegerField(default=0, help_text="Display order on homepage")

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("library:category_detail", kwargs={"slug": self.slug})

    @property
    def approved_book_count(self):
        return self.books.filter(status="approved").count()


class Scholar(models.Model):
    """
    Islamic scholars / authors — both religious and scientific.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    birth_year = models.IntegerField(null=True, blank=True, help_text="Birth year (Gregorian)")
    death_year = models.IntegerField(null=True, blank=True, help_text="Death year (Gregorian)")
    bio = models.TextField(blank=True, help_text="Brief biography")
    bio_views = models.PositiveIntegerField(default=0, help_text="Number of times the biography has been viewed")
    field_of_expertise = models.CharField(
        max_length=200,
        blank=True,
        help_text="Primary field of expertise (e.g., Medicine, Astronomy, Hadith)"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        years = ""
        if self.birth_year or self.death_year:
            b = self.birth_year or "?"
            d = self.death_year or "?"
            years = f" ({b} - {d})"
        return f"{self.name}{years}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Scholar.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("library:scholar_detail", kwargs={"slug": self.slug})

    def increment_bio_views(self):
        """Increment biography view count atomically."""
        Scholar.objects.filter(pk=self.pk).update(bio_views=models.F("bio_views") + 1)


class Language(models.Model):
    """
    Languages available for books (Arabic, English, Urdu, etc.)
    """
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(
        max_length=10,
        blank=True,
        help_text="ISO language code (e.g., 'ar', 'en')"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


def book_upload_path(instance, filename):
    """Path: books/{domain}/{category}/{scholar}/{slug}.pdf"""
    # Ensure domain is synced
    if not instance.knowledge_domain and instance.category:
        domain_obj = instance.category.knowledge_domain
        domain_name = domain_obj.name if domain_obj else "unknown-domain"
    elif instance.knowledge_domain:
        domain_name = instance.knowledge_domain.name
    else:
        domain_name = "unknown-domain"

    domain = slugify(domain_name)
    category = slugify(instance.category.name) if instance.category else "unknown-category"
    scholar = slugify(instance.scholar.name) if instance.scholar else "unknown-scholar"
    slug = instance.slug or slugify(instance.title)
    
    ext = filename.split('.')[-1]
    return f"books/{domain}/{category}/{scholar}/{slug}.{ext}"


def cover_upload_path(instance, filename):
    """Path: covers/{domain}/{category}/{slug}.jpg"""
    if not instance.knowledge_domain and instance.category:
        domain_obj = instance.category.knowledge_domain
        domain_name = domain_obj.name if domain_obj else "unknown-domain"
    elif instance.knowledge_domain:
        domain_name = instance.knowledge_domain.name
    else:
        domain_name = "unknown-domain"

    domain = slugify(domain_name)
    category = slugify(instance.category.name) if instance.category else "unknown-category"
    slug = instance.slug or slugify(instance.title)
    
    ext = filename.split('.')[-1]
    return f"covers/{domain}/{category}/{slug}.{ext}"


class Book(models.Model):
    """
    Main book model for the Islamic Digital Library.
    """
    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    # Core fields
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    description = models.TextField(blank=True, help_text="Brief description of the book")

    # Relationships
    knowledge_domain = models.ForeignKey(
        KnowledgeDomain,
        on_delete=models.CASCADE,
        related_name="books",
        null=True,
        blank=True,
        help_text="Knowledge domain (Religious Knowledge / Islamic Sciences)"
    )
    scholar = models.ForeignKey(
        Scholar,
        on_delete=models.CASCADE,
        related_name="books",
        help_text="Author / Scholar"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="books"
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="books"
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="uploaded_books"
    )

    # Files
    pdf_file = models.FileField(
        upload_to=book_upload_path,
        validators=[validate_pdf_file, validate_file_size],
        help_text="Upload PDF file (max 50MB)"
    )
    cover_image = models.ImageField(
        upload_to=cover_upload_path,
        blank=True,
        null=True,
        help_text="Book cover image (optional)"
    )

    # Moderation
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True
    )

    # Featured
    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Mark as featured to display on homepage"
    )

    # Statistics
    views = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["-downloads"]),
            models.Index(fields=["-views"]),
            models.Index(fields=["is_featured", "-created_at"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-set knowledge_domain from category if not explicitly set
        if not self.knowledge_domain_id and self.category_id:
            self.knowledge_domain = self.category.knowledge_domain

        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Book.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("library:book_detail", kwargs={"slug": self.slug})

    @property
    def is_approved(self):
        return self.status == "approved"

    def increment_views(self):
        """Increment view count atomically."""
        Book.objects.filter(pk=self.pk).update(views=models.F("views") + 1)

    def increment_downloads(self):
        """Increment download count atomically."""
        Book.objects.filter(pk=self.pk).update(downloads=models.F("downloads") + 1)


class BookBookmark(models.Model):
    """
    Allows logged-in users to bookmark / save books to their personal library.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bookmarks"
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="bookmarks"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "book")
        ordering = ["-created_at"]
        verbose_name = "Bookmark"
        verbose_name_plural = "Bookmarks"

    def __str__(self):
        return f"{self.user.username} → {self.book.title}"


class LibraryFeedback(models.Model):
    """
    Community feedback / suggestions for improving the library.
    Supports both authenticated users and guest submissions.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedbacks",
        help_text="Logged-in user (auto-filled, null for guests)"
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name (optional for logged-in users)"
    )
    email = models.EmailField(
        blank=True,
        help_text="Email for follow-up (optional)"
    )
    message = models.TextField(
        max_length=2000,
        help_text="Suggestion or feedback (max 2000 characters)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Library Feedback"
        verbose_name_plural = "Library Feedbacks"

    def __str__(self):
        sender = self.user.username if self.user else (self.name or "Anonymous")
        return f"Feedback from {sender} — {self.created_at:%Y-%m-%d}"


class IssueReport(models.Model):
    """
    Issue reports submitted by the community.
    Supports structured issue types and optional book references.
    """
    ISSUE_TYPE_CHOICES = [
        ("wrong_pdf", "Wrong PDF"),
        ("duplicate_book", "Duplicate Book"),
        ("incorrect_scholar", "Incorrect Scholar"),
        ("broken_download", "Broken Download"),
        ("copyright_concern", "Copyright Concern"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("dismissed", "Dismissed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issue_reports",
        help_text="Logged-in user (auto-filled, null for guests)"
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name (optional for logged-in users)"
    )
    email = models.EmailField(
        blank=True,
        help_text="Email for follow-up (optional)"
    )
    issue_type = models.CharField(
        max_length=30,
        choices=ISSUE_TYPE_CHOICES,
        default="other",
        db_index=True,
        help_text="Category of the issue"
    )
    message = models.TextField(
        max_length=2000,
        help_text="Describe the issue in detail (max 2000 characters)"
    )
    related_book = models.ForeignKey(
        Book,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issue_reports",
        help_text="The book this issue relates to (if applicable)"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="open",
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Issue Report"
        verbose_name_plural = "Issue Reports"

    def __str__(self):
        sender = self.user.username if self.user else (self.name or "Anonymous")
        return f"{self.get_issue_type_display()} — {sender} — {self.created_at:%Y-%m-%d}"
