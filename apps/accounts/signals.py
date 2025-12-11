from allauth.socialaccount.signals import social_account_added, social_account_updated
from django.dispatch import receiver


@receiver(social_account_added)
@receiver(social_account_updated)
def populate_user_name(request, sociallogin, **kwargs):
    user = sociallogin.user
    data = sociallogin.account.extra_data

    if not user.full_name:
        user.full_name = data.get("name", "")
        user.save()