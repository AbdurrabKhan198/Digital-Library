from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import ScholarArticle, ScholarArticleComment

class ArticleListView(ListView):
    model = ScholarArticle
    template_name = 'blog/article_list.html'
    context_object_name = 'articles'
    paginate_by = 9

    def get_queryset(self):
        queryset = ScholarArticle.objects.filter(is_published=True)
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(scholar__name__icontains=query) |
                Q(short_description__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context

class ArticleDetailView(DetailView):
    model = ScholarArticle
    template_name = 'blog/article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        # Allow authors to see their own unpublished articles? 
        # For now, stick to requirements: published only for public.
        return ScholarArticle.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.filter(is_approved=True)
        return context

@login_required
def add_comment(request, slug):
    article = get_object_or_404(ScholarArticle, slug=slug, is_published=True)
    if request.method == 'POST':
        comment_text = request.POST.get('comment_text')
        if comment_text:
            ScholarArticleComment.objects.create(
                article=article,
                user=request.user,
                comment_text=comment_text
            )
    return redirect('blog:article_detail', slug=slug)
