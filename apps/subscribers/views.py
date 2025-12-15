from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Subscriber
from .forms import SubscribeForm
from .emails import send_newsletter
from apps.articles.models import Tag


def subscribe(request):
    if request.method == "POST":
        form = SubscribeForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            subscriber, created = Subscriber.objects.get_or_create(email=email)
            if created:
                send_newsletter(
                    subscriber.email,
                    "Welcome to i33ym",
                    """
                    <h2>Thanks for subscribing!</h2>
                    <p>You'll receive updates when I publish new essays.</p>
                    <p><a href="https://i33ym.cc/newsletter/preferences/{}/">Set your preferences</a> to choose which topics you'd like to follow.</p>
                    """.format(subscriber.token),
                    subscriber.token
                )
                messages.success(request, "Check your email to confirm your subscription.")
            else:
                messages.info(request, "You're already subscribed.")
            return redirect("subscribers:preferences", token=subscriber.token)
    else:
        form = SubscribeForm()
    return render(request, "subscribers/subscribe.html", {"form": form})


def preferences(request, token):
    subscriber = get_object_or_404(Subscriber, token=token)
    tags = Tag.objects.all()

    if request.method == "POST":
        selected_tags = request.POST.getlist("tags")
        subscriber.tags.set(selected_tags)
        subscriber.is_confirmed = True
        subscriber.save()
        messages.success(request, "Your preferences have been saved.")
        return redirect("subscribers:preferences", token=token)

    return render(request, "subscribers/preferences.html", {
        "subscriber": subscriber,
        "tags": tags,
    })


def unsubscribe(request, token):
    subscriber = get_object_or_404(Subscriber, token=token)
    if request.method == "POST":
        subscriber.delete()
        messages.success(request, "You have been unsubscribed.")
        return redirect("articles:home")
    return render(request, "subscribers/unsubscribe.html", {"subscriber": subscriber})