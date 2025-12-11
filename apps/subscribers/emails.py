import resend
from django.conf import settings


def send_newsletter(subscriber_email, subject, html_content):
    if not settings.RESEND_API_KEY:
        return None

    resend.api_key = settings.RESEND_API_KEY

    params = {
        "from": "i33ym <blog@i33ym.cc>",
        "to": [subscriber_email],
        "subject": subject,
        "html": html_content,
    }

    return resend.Emails.send(params)


def send_to_tag_subscribers(tag, article):
    from .models import Subscriber

    subscribers = Subscriber.objects.filter(is_confirmed=True, tags=tag)
    subject = f"New essay: {article.title}"

    html_content = f"""
    <h2>{article.title}</h2>
    <p>{article.excerpt}</p>
    <p><a href="https://i33ym.cc/{article.slug}/">Read more →</a></p>
    <hr>
    <p style="color: #888; font-size: 12px;">
        You received this because you subscribed to "{tag.name}" on i33ym.cc
    </p>
    """

    for subscriber in subscribers:
        send_newsletter(subscriber.email, subject, html_content)