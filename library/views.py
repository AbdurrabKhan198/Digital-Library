"""
Views for the Islamic Digital Library.

All views use class-based views for clean, reusable code.
Supports Knowledge Domain filtering, bookmarks, PDF reading,
and community feedback.
"""

from django.views.generic import (
    ListView, DetailView, CreateView, TemplateView, FormView, View
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, F, Count, Sum
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse, FileResponse
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.conf import settings
from django.contrib.auth.models import User

from .models import Book, Category, Scholar, Language, KnowledgeDomain, BookBookmark
from .forms import BookUploadForm, FeedbackForm, IssueReportForm


class HomePageView(TemplateView):
    """
    Homepage with hero search, featured books, domain-grouped categories,
    popular & recent books.
    """
    template_name = "library/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        approved = Book.objects.filter(status="approved")

        # Domain-grouped categories
        context["knowledge_domains"] = (
            KnowledgeDomain.objects.prefetch_related("categories").all()
        )

        # Flat categories for backward compat
        context["categories"] = Category.objects.select_related("knowledge_domain").all()

        # Featured Books (new)
        context["featured_books"] = (
            approved.filter(is_featured=True)
            .select_related("scholar", "category", "language")
            .order_by("-created_at")[:10]
        )

        context["popular_books"] = (
            approved.order_by("-downloads")
            .select_related("scholar", "category", "language")[:10]
        )
        context["recent_books"] = (
            approved.order_by("-created_at")
            .select_related("scholar", "category", "language")[:4]
        )
        context["total_books"] = approved.count()
        context["total_scholars"] = Scholar.objects.count()
        context["total_categories"] = Category.objects.count()
        context["total_domains"] = KnowledgeDomain.objects.count()
        return context


class BookListView(ListView):
    """
    Paginated list of approved books with filtering support.
    Includes Knowledge Domain filtering.
    """
    model = Book
    template_name = "library/book_list.html"
    context_object_name = "books"
    paginate_by = 20

    def get_queryset(self):
        queryset = Book.objects.filter(status="approved").select_related(
            "scholar", "category", "language", "uploaded_by", "knowledge_domain"
        )

        # Search
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(scholar__name__icontains=query) |
                Q(category__name__icontains=query) |
                Q(description__icontains=query)
            )

        # Filter by knowledge domain
        domain = self.request.GET.get("domain", "")
        if domain:
            queryset = queryset.filter(knowledge_domain__slug=domain)

        # Filter by category
        category = self.request.GET.get("category", "")
        if category:
            queryset = queryset.filter(category__slug=category)

        # Filter by scholar
        scholar = self.request.GET.get("scholar", "")
        if scholar:
            queryset = queryset.filter(scholar__slug=scholar)

        # Filter by language
        language = self.request.GET.get("language", "")
        if language:
            queryset = queryset.filter(language__id=language)

        # Sorting
        sort = self.request.GET.get("sort", "-created_at")
        valid_sorts = [
            "title", "-title",
            "-created_at", "created_at",
            "-downloads", "-views"
        ]
        if sort in valid_sorts:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["knowledge_domains"] = KnowledgeDomain.objects.all()
        context["categories"] = Category.objects.select_related("knowledge_domain").all()
        context["scholars"] = Scholar.objects.all()
        context["languages"] = Language.objects.all()
        context["current_query"] = self.request.GET.get("q", "")
        context["current_domain"] = self.request.GET.get("domain", "")
        context["current_category"] = self.request.GET.get("category", "")
        context["current_scholar"] = self.request.GET.get("scholar", "")
        context["current_language"] = self.request.GET.get("language", "")
        context["current_sort"] = self.request.GET.get("sort", "-created_at")
        return context


class BookDetailView(DetailView):
    """
    Detailed view of a single book.
    Only shows approved books to non-staff users.
    Increments view count on each visit.
    """
    model = Book
    template_name = "library/book_detail.html"
    context_object_name = "book"

    def get_queryset(self):
        if self.request.user.is_staff:
            return Book.objects.select_related(
                "scholar", "category", "language", "uploaded_by",
                "knowledge_domain"
            )
        return Book.objects.filter(status="approved").select_related(
            "scholar", "category", "language", "uploaded_by",
            "knowledge_domain"
        )

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Increment view count
        self.object.increment_views()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Related books in the same category
        context["related_books"] = (
            Book.objects.filter(
                status="approved",
                category=self.object.category
            )
            .exclude(pk=self.object.pk)
            .select_related("scholar")[:4]
        )
        # Check if user has bookmarked this book
        if self.request.user.is_authenticated:
            context["is_bookmarked"] = BookBookmark.objects.filter(
                user=self.request.user, book=self.object
            ).exists()
        else:
            context["is_bookmarked"] = False
        return context


class BookUploadView(LoginRequiredMixin, CreateView):
    """
    Upload a new book. Only accessible to authenticated users.
    Books start with 'pending' status and require admin approval.
    """
    model = Book
    form_class = BookUploadForm
    template_name = "library/book_upload.html"
    success_url = reverse_lazy("library:upload_success")

    def form_valid(self, form):
        # Check for duplicates
        duplicates = form.check_duplicate()
        if duplicates and not self.request.POST.get("confirm_duplicate"):
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    duplicates=duplicates,
                    show_duplicate_warning=True
                )
            )

        # Set the uploader, status, and domain from selected category
        form.instance.uploaded_by = self.request.user
        form.instance.status = "pending"

        # Set knowledge_domain from the form's domain field
        domain = form.cleaned_data.get("knowledge_domain")
        if domain:
            form.instance.knowledge_domain = domain

        messages.success(
            self.request,
            "Your book has been uploaded successfully! "
            "It will be visible after admin approval."
        )
        return super().form_valid(form)


class UploadSuccessView(LoginRequiredMixin, TemplateView):
    """Success page shown after book upload."""
    template_name = "library/upload_success.html"


class CategoryDetailView(TemplateView):
    """
    Enhanced category landing page with featured, popular,
    and recently added books within this category.
    """
    template_name = "library/category_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(
            Category.objects.select_related("knowledge_domain"),
            slug=self.kwargs["slug"]
        )
        context["category"] = category

        approved_in_cat = Book.objects.filter(
            status="approved", category=category
        ).select_related("scholar", "language")

        context["total_books"] = approved_in_cat.count()
        context["featured_books"] = (
            approved_in_cat.filter(is_featured=True)
            .order_by("-created_at")[:4]
        )
        context["popular_books"] = approved_in_cat.order_by("-downloads")[:8]
        context["recent_books"] = approved_in_cat.order_by("-created_at")[:4]
        return context


class ScholarListView(ListView):
    """
    Paginated list of all scholars with search support.
    """
    model = Scholar
    template_name = "library/scholar_list.html"
    context_object_name = "scholars"
    paginate_by = 24

    def get_queryset(self):
        queryset = Scholar.objects.annotate(
            book_count=Count('books', filter=Q(books__status='approved'))
        ).order_by('name')

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(field_of_expertise__icontains=query) |
                Q(bio__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_query"] = self.request.GET.get("q", "")
        context["total_scholars"] = self.get_queryset().count()
        return context


class ScholarDetailView(TemplateView):
    """
    Public scholar profile page showing:
    - full bio, field of expertise, life years
    - total books count
    - list of all books by this scholar
    """
    template_name = "library/scholar_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scholar = get_object_or_404(Scholar, slug=self.kwargs["slug"])
        context["scholar"] = scholar

        # Increment biography view count
        scholar.increment_bio_views()
        # Refresh to get the updated count
        scholar.refresh_from_db(fields=["bio_views"])
        context["bio_views"] = scholar.bio_views

        books = (
            Book.objects.filter(status="approved", scholar=scholar)
            .select_related("category", "language")
            .order_by("-created_at")
        )
        context["books"] = books
        context["total_books"] = books.count()
        context["total_views"] = books.aggregate(Sum("views"))["views__sum"] or 0
        context["total_downloads"] = books.aggregate(Sum("downloads"))["downloads__sum"] or 0
        return context


class SearchView(BookListView):
    """
    Search results page - extends BookListView with search context.
    """
    template_name = "library/search_results.html"


# =========================================================================
# PDF READER & PREVIEW
# =========================================================================

class ReadOnlineView(DetailView):
    """
    Online PDF reader using PDF.js.
    Shows the full PDF in a browser-based reader.
    """
    model = Book
    template_name = "library/read_online.html"
    context_object_name = "book"

    def get_queryset(self):
        return Book.objects.filter(status="approved").select_related(
            "scholar", "category"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["preview_mode"] = False
        context["pdf_url"] = reverse("library:book_pdf_proxy", kwargs={"slug": self.object.slug})
        return context


class PreviewBookView(DetailView):
    """
    Preview mode — loads PDF.js with first 5 pages only.
    """
    model = Book
    template_name = "library/read_online.html"
    context_object_name = "book"

    def get_queryset(self):
        return Book.objects.filter(status="approved").select_related(
            "scholar", "category"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["preview_mode"] = True
        context["max_pages"] = 5
        context["pdf_url"] = reverse("library:book_pdf_proxy", kwargs={"slug": self.object.slug})
        return context

def pdf_proxy(request, slug):
    """
    Proxy view to serve S3 PDFs via Django to bypass CORS limitations.
    Fetches the file from S3 using boto3 and streams it to the browser.
    """
    book = get_object_or_404(Book, slug=slug, status="approved")
    
    if settings.USE_S3:
        import boto3
        from botocore.exceptions import ClientError
        
        # Initialize S3-compatible client (Cloudflare R2)
        s3_kwargs = {
            'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
            'region_name': settings.AWS_S3_REGION_NAME,
        }
        # R2 requires the endpoint_url to route requests to Cloudflare
        if hasattr(settings, 'AWS_S3_ENDPOINT_URL'):
            s3_kwargs['endpoint_url'] = settings.AWS_S3_ENDPOINT_URL
        
        s3 = boto3.client('s3', **s3_kwargs)
        
        try:
            # The S3 Key is the pdf_file.name (maybe prefixed with AWS_LOCATION)
            file_key = book.pdf_file.name
            
            # Ensure the media prefix is included if using R2 and it's not already there
            remote_prefix = getattr(settings, 'AWS_LOCATION', '')
            if remote_prefix and not file_key.startswith(remote_prefix):
                file_key = f"{remote_prefix}/{file_key}".replace("//", "/")
            
            s3_response = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_key)
            
            # Stream the Body (StreamingBody) directly to the client
            response = StreamingHttpResponse(
                s3_response['Body'],
                content_type='application/pdf'
            )
            
            # Add headers for inline viewing and content length
            response['Content-Disposition'] = f'inline; filename="{slug}.pdf"'
            if 'ContentLength' in s3_response:
                response['Content-Length'] = s3_response['ContentLength']
                
            return response
            
        except ClientError as e:
            return HttpResponse(f"S3 Error: {str(e)}", status=502)
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=500)
            
    # Local storage fallback
    try:
        return FileResponse(book.pdf_file.open('rb'), content_type='application/pdf')
    except FileNotFoundError:
        return HttpResponse("PDF file not found.", status=404)


# =========================================================================
# BOOKMARKS
# =========================================================================

class ToggleBookmarkView(LoginRequiredMixin, View):
    """
    AJAX endpoint to toggle a bookmark on/off.
    Returns JSON with the new bookmark status.
    """
    def post(self, request, slug):
        book = get_object_or_404(Book, slug=slug, status="approved")
        bookmark, created = BookBookmark.objects.get_or_create(
            user=request.user, book=book
        )
        if not created:
            bookmark.delete()
            return JsonResponse({"bookmarked": False})
        return JsonResponse({"bookmarked": True})


class MyLibraryView(LoginRequiredMixin, ListView):
    """
    Personal library page showing user's bookmarked books.
    """
    template_name = "library/my_library.html"
    context_object_name = "bookmarks"
    paginate_by = 20

    def get_queryset(self):
        return (
            BookBookmark.objects.filter(user=self.request.user)
            .select_related("book__scholar", "book__category", "book__language")
            .order_by("-created_at")
        )


# =========================================================================
# STATIC PAGES
# =========================================================================

class UploadGuidelinesView(TemplateView):
    """Upload guidelines static page."""
    template_name = "library/upload_guidelines.html"


# =========================================================================
# DOWNLOAD HANDLER + AJAX ENDPOINTS
# =========================================================================

def download_book(request, slug):
    """
    Track download and redirect to the PDF file.
    """
    book = get_object_or_404(Book, slug=slug, status="approved")
    book.increment_downloads()
    return redirect(book.pdf_file.url)


def check_duplicate_ajax(request):
    """
    AJAX endpoint for real-time duplicate checking during upload.
    """
    title = request.GET.get("title", "").strip()
    scholar_id = request.GET.get("scholar", "")

    if title and scholar_id:
        exists = Book.objects.filter(
            title__iexact=title,
            scholar_id=scholar_id
        ).exclude(status="rejected").exists()
        return JsonResponse({"duplicate": exists})

    return JsonResponse({"duplicate": False})


def get_categories_by_domain(request):
    """
    AJAX endpoint: return categories for a selected knowledge domain.
    Used in the upload form to dynamically filter the category dropdown.
    """
    domain_id = request.GET.get("domain_id", "")
    categories = []

    if domain_id:
        cats = Category.objects.filter(knowledge_domain_id=domain_id).order_by("order", "name")
        categories = [{"id": c.id, "name": c.name} for c in cats]

    return JsonResponse({"categories": categories})


# =========================================================================
# COMMUNITY FEEDBACK VIEWS
# =========================================================================

class FeedbackView(FormView):
    """
    Page for submitting library improvement suggestions.
    Open to all users (authenticated and guests).
    """
    template_name = "library/feedback.html"
    form_class = FeedbackForm
    success_url = reverse_lazy("library:feedback")

    def form_valid(self, form):
        # Simple session-based rate limiting: max 5 submissions per session
        count = self.request.session.get("feedback_count", 0)
        if count >= 5:
            messages.error(
                self.request,
                "You have reached the maximum number of feedback submissions "
                "for this session. Please try again later."
            )
            return self.form_invalid(form)

        feedback = form.save(commit=False)

        # Auto-attach user if logged in
        if self.request.user.is_authenticated:
            feedback.user = self.request.user
            if not feedback.name:
                feedback.name = self.request.user.username
            if not feedback.email:
                feedback.email = self.request.user.email or ""

        feedback.save()

        # Increment session counter
        self.request.session["feedback_count"] = count + 1

        messages.success(
            self.request,
            "JazakAllahu Khairan! Thank you for helping improve this library. "
            "Your suggestion has been received."
        )
        return super().form_valid(form)


class ReportIssueView(FormView):
    """
    Page for reporting issues with books or the platform.
    Open to all users (authenticated and guests).
    """
    template_name = "library/report_issue.html"
    form_class = IssueReportForm
    success_url = reverse_lazy("library:report_issue")

    def get_initial(self):
        initial = super().get_initial()
        # Pre-select book if provided via query param (e.g., from book detail page)
        book_slug = self.request.GET.get("book")
        if book_slug:
            try:
                book = Book.objects.get(slug=book_slug, status="approved")
                initial["related_book"] = book.pk
            except Book.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        # Session-based rate limiting
        count = self.request.session.get("report_count", 0)
        if count >= 5:
            messages.error(
                self.request,
                "You have reached the maximum number of reports "
                "for this session. Please try again later."
            )
            return self.form_invalid(form)

        report = form.save(commit=False)

        # Auto-attach user if logged in
        if self.request.user.is_authenticated:
            report.user = self.request.user
            if not report.name:
                report.name = self.request.user.username
            if not report.email:
                report.email = self.request.user.email or ""

        report.save()

        self.request.session["report_count"] = count + 1

        messages.success(
            self.request,
            "Thank you for reporting this issue. "
            "Our team will review it and take action as needed."
        )
        return super().form_valid(form)
