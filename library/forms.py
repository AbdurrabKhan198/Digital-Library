"""
Forms for the Islamic Digital Library.

Includes book upload form with domain-aware category selection
and duplicate detection.
"""

from django import forms
from .models import Book, Scholar, KnowledgeDomain, Category, LibraryFeedback, IssueReport

# Reusable TailwindCSS classes for form inputs
INPUT_CLASS = (
    "w-full px-4 py-3 rounded-xl border border-gray-200 "
    "focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 "
    "transition-all duration-200 bg-white"
)

FILE_CLASS = (
    "w-full px-4 py-3 rounded-xl border border-gray-200 "
    "focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 "
    "transition-all duration-200 bg-white file:mr-4 file:py-2 "
    "file:px-4 file:rounded-lg file:border-0 file:bg-emerald-50 "
    "file:text-emerald-700 hover:file:bg-emerald-100"
)


class BookUploadForm(forms.ModelForm):
    """
    Form for uploading new books to the library.
    Includes domain-aware category selection and duplicate detection.
    """

    # Knowledge domain selector (not a model field on Book, used to filter categories)
    knowledge_domain = forms.ModelChoiceField(
        queryset=KnowledgeDomain.objects.all(),
        required=True,
        empty_label="-- Select a knowledge domain --",
        widget=forms.Select(attrs={
            "class": INPUT_CLASS,
            "id": "id_knowledge_domain",
        }),
        help_text="Choose the knowledge domain first to filter categories."
    )

    # Allow user to type a new scholar name if not in the list
    new_scholar_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            "class": INPUT_CLASS,
            "placeholder": "Or enter a new scholar name...",
        }),
        help_text="If the scholar is not listed above, enter their name here."
    )

    class Meta:
        model = Book
        fields = [
            "title",
            "scholar",
            "category",
            "language",
            "description",
            "pdf_file",
            "cover_image",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": INPUT_CLASS,
                "placeholder": "Enter book title...",
            }),
            "scholar": forms.Select(attrs={"class": INPUT_CLASS}),
            "category": forms.Select(attrs={
                "class": INPUT_CLASS,
                "id": "id_category",
            }),
            "language": forms.Select(attrs={"class": INPUT_CLASS}),
            "description": forms.Textarea(attrs={
                "class": INPUT_CLASS,
                "rows": 4,
                "placeholder": "Brief description of the book...",
            }),
            "pdf_file": forms.ClearableFileInput(attrs={
                "class": FILE_CLASS,
                "accept": ".pdf",
            }),
            "cover_image": forms.ClearableFileInput(attrs={
                "class": FILE_CLASS,
                "accept": "image/*",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make scholar optional (user can provide new_scholar_name instead)
        self.fields["scholar"].required = False
        self.fields["scholar"].empty_label = "-- Select a scholar --"
        self.fields["category"].empty_label = "-- Select a category --"
        self.fields["language"].empty_label = "-- Select a language --"

        # If form was submitted with a domain, filter categories to that domain
        if "knowledge_domain" in self.data:
            try:
                domain_id = int(self.data.get("knowledge_domain"))
                self.fields["category"].queryset = Category.objects.filter(
                    knowledge_domain_id=domain_id
                )
            except (ValueError, TypeError):
                self.fields["category"].queryset = Category.objects.all()
        elif self.instance.pk and self.instance.category_id:
            # Editing: pre-filter categories by the book's domain
            self.fields["category"].queryset = Category.objects.filter(
                knowledge_domain=self.instance.category.knowledge_domain
            )

    def clean(self):
        cleaned_data = super().clean()
        scholar = cleaned_data.get("scholar")
        new_scholar_name = cleaned_data.get("new_scholar_name", "").strip()

        # Ensure either scholar is selected or new name is provided
        if not scholar and not new_scholar_name:
            raise forms.ValidationError(
                "Please select an existing scholar or enter a new scholar name."
            )

        # If new scholar name is given, create the scholar
        if new_scholar_name and not scholar:
            scholar_obj, created = Scholar.objects.get_or_create(
                name=new_scholar_name
            )
            cleaned_data["scholar"] = scholar_obj

        return cleaned_data

    def check_duplicate(self):
        """
        Check if a similar book already exists.
        Returns matching books or None.
        """
        title = self.cleaned_data.get("title", "")
        scholar = self.cleaned_data.get("scholar")

        if title and scholar:
            duplicates = Book.objects.filter(
                title__iexact=title,
                scholar=scholar
            ).exclude(status="rejected")
            if duplicates.exists():
                return duplicates
        return None


# =========================================================================
# COMMUNITY FEEDBACK FORMS
# =========================================================================

class FeedbackForm(forms.ModelForm):
    """
    Form for submitting library improvement suggestions.
    Includes honeypot spam protection and message length validation.
    """

    # Honeypot field — hidden from real users, bots fill it in
    website = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"tabindex": "-1", "autocomplete": "off"}),
    )

    class Meta:
        model = LibraryFeedback
        fields = ["name", "email", "message"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": INPUT_CLASS,
                "placeholder": "Your name (optional)",
            }),
            "email": forms.EmailInput(attrs={
                "class": INPUT_CLASS,
                "placeholder": "your@email.com (optional)",
            }),
            "message": forms.Textarea(attrs={
                "class": INPUT_CLASS,
                "rows": 5,
                "placeholder": "Share your suggestion — new features, missing categories, search improvements, new languages or scholars...",
                "maxlength": "2000",
            }),
        }

    def clean_message(self):
        message = self.cleaned_data.get("message", "").strip()
        if len(message) < 10:
            raise forms.ValidationError(
                "Please provide at least 10 characters so we can understand your suggestion."
            )
        return message

    def clean(self):
        cleaned_data = super().clean()
        # Honeypot check — if filled, it's a bot
        if cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return cleaned_data


class IssueReportForm(forms.ModelForm):
    """
    Form for reporting issues with books or the platform.
    Includes issue type selection, optional book picker, and spam protection.
    """

    # Honeypot field
    website = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"tabindex": "-1", "autocomplete": "off"}),
    )

    class Meta:
        model = IssueReport
        fields = ["name", "email", "issue_type", "related_book", "message"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": INPUT_CLASS,
                "placeholder": "Your name (optional)",
            }),
            "email": forms.EmailInput(attrs={
                "class": INPUT_CLASS,
                "placeholder": "your@email.com (optional)",
            }),
            "issue_type": forms.Select(attrs={
                "class": INPUT_CLASS,
            }),
            "related_book": forms.Select(attrs={
                "class": INPUT_CLASS,
            }),
            "message": forms.Textarea(attrs={
                "class": INPUT_CLASS,
                "rows": 5,
                "placeholder": "Describe the issue in detail...",
                "maxlength": "2000",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["related_book"].required = False
        self.fields["related_book"].empty_label = "-- Select a book (optional) --"
        self.fields["related_book"].queryset = Book.objects.filter(
            status="approved"
        ).select_related("scholar").order_by("title")

    def clean_message(self):
        message = self.cleaned_data.get("message", "").strip()
        if len(message) < 10:
            raise forms.ValidationError(
                "Please provide at least 10 characters so we can understand the issue."
            )
        return message

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return cleaned_data
