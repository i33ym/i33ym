from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from apps.articles.models import Article
from .models import Reaction


@login_required
def toggle_reaction(request, slug, reaction_type):
    if reaction_type not in ["like", "dislike"]:
        return redirect("articles:detail", slug=slug)

    article = get_object_or_404(Article, slug=slug, status=Article.Status.PUBLISHED)
    is_anonymous = request.POST.get("anonymous") == "on"

    existing = Reaction.objects.filter(article=article, user=request.user).first()

    if existing:
        if existing.type == reaction_type:
            existing.delete()
        else:
            existing.type = reaction_type
            existing.is_anonymous = is_anonymous
            existing.save()
    else:
        Reaction.objects.create(
            article=article,
            user=request.user,
            type=reaction_type,
            is_anonymous=is_anonymous
        )

    return redirect("articles:detail", slug=slug)