"""
Context processors for the Islamic Digital Library.

Provides global template variables available in all templates.
"""

from .models import Category, KnowledgeDomain


def global_context(request):
    """
    Add global context variables to all templates.
    Includes domain-grouped categories for navigation.
    """
    return {
        "all_categories": Category.objects.select_related("knowledge_domain").all()[:20],
        "all_domains": KnowledgeDomain.objects.prefetch_related("categories").all(),
        "site_name": "Bayt al-Hikmah Online",
    }
