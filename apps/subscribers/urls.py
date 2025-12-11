from django.urls import path
from . import views

app_name = "subscribers"

urlpatterns = [
    path("subscribe/", views.subscribe, name="subscribe"),
    path("preferences/<str:token>/", views.preferences, name="preferences"),
    path("unsubscribe/<str:token>/", views.unsubscribe, name="unsubscribe"),
]