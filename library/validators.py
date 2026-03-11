"""
File validators for the Islamic Digital Library.

Ensures only valid PDF files under 50MB are uploaded.
"""

from django.core.exceptions import ValidationError


def validate_pdf_file(value):
    """
    Validate that the uploaded file is a PDF.
    Checks both the file extension and content type.
    """
    import os

    ext = os.path.splitext(value.name)[1].lower()
    if ext != ".pdf":
        raise ValidationError(
            "Only PDF files are allowed. Please upload a file with .pdf extension."
        )

    # Check content type if available
    if hasattr(value, "content_type"):
        if value.content_type != "application/pdf":
            raise ValidationError(
                "Invalid file type. Please upload a valid PDF file."
            )


def validate_file_size(value):
    """
    Validate that the uploaded file does not exceed 50MB.
    """
    max_size = 50 * 1024 * 1024  # 50MB in bytes

    if value.size > max_size:
        raise ValidationError(
            f"File size exceeds the maximum limit of 50MB. "
            f"Your file is {value.size / (1024 * 1024):.1f}MB."
        )
