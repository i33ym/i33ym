import resend
from django.conf import settings


def send_newsletter(subscriber_email, subject, html_content, unsubscribe_token=None):
    if not settings.RESEND_API_KEY:
        print("RESEND_API_KEY not configured")
        return None

    resend.api_key = settings.RESEND_API_KEY

    if unsubscribe_token:
        html_content += f'''
        <hr style="margin-top: 40px; border: none; border-top: 1px solid #eee;">
        <p style="color: #888; font-size: 12px; margin-top: 20px;">
            <a href="https://i33ym.cc/newsletter/unsubscribe/{unsubscribe_token}/">Unsubscribe</a>
        </p>
        '''

    params = {
        "from": "i33ym <noreply@news.i33ym.cc>",
        "to": [subscriber_email],
        "subject": subject,
        "html": html_content,
    }

    try:
        return resend.Emails.send(params)
    except Exception as e:
        print(f"Email error: {e}")
        return None


def notify_subscribers_new_article(article):
    from .models import Subscriber

    subscribers = Subscriber.objects.filter(
        is_confirmed=True,
        tags__in=article.tags.all()
    ).distinct()

    subject = f"New essay: {article.title}"

    for subscriber in subscribers:
        html_content = f'''
        <h2 style="font-family: Georgia, serif; color: #2c2c2c;">{article.title}</h2>
        <p style="font-family: Georgia, serif; color: #555; line-height: 1.7;">{article.excerpt}</p>
        <p style="margin-top: 20px;">
            <a href="https://i33ym.cc/{article.slug}/" style="color: #2c2c2c;">Read more →</a>
        </p>
        '''
        send_newsletter(subscriber.email, subject, html_content, subscriber.token)