from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Article, Tag
from apps.comments.forms import CommentForm
from apps.reactions.models import Reaction


def home(request):
    articles = Article.objects.filter(status=Article.Status.PUBLISHED).select_related("author").prefetch_related("tags")
    return render(request, "articles/home.html", {"articles": articles})


def articles_by_tag(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    articles = tag.articles.filter(status=Article.Status.PUBLISHED).select_related("author")
    return render(request, "articles/by_tag.html", {"tag": tag, "articles": articles})


def article_detail(request, slug):
    article = get_object_or_404(
        Article.objects.select_related("author").prefetch_related("tags", "comments__user"),
        slug=slug,
        status=Article.Status.PUBLISHED
    )
    comments = article.comments.filter(is_approved=True).select_related("user")
    form = CommentForm()

    likes = article.reactions.filter(type=Reaction.Type.LIKE).count()
    dislikes = article.reactions.filter(type=Reaction.Type.DISLIKE).count()
    user_reaction = None
    if request.user.is_authenticated:
        reaction = article.reactions.filter(user=request.user).first()
        if reaction:
            user_reaction = reaction.type

    return render(request, "articles/detail.html", {
        "article": article,
        "comments": comments,
        "form": form,
        "likes": likes,
        "dislikes": dislikes,
        "user_reaction": user_reaction,
    })


@login_required
def add_comment(request, slug):
    article = get_object_or_404(Article, slug=slug, status=Article.Status.PUBLISHED)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.user = request.user
            comment.save()
    return redirect("articles:detail", slug=slug)

def about(request):
    return render(request, "articles/about.html")