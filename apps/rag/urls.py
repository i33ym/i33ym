from django.urls import path
from . import views

app_name = "rag"

urlpatterns = [
    path("", views.chat_page, name="chat"),
    path("api/query/", views.chat_api, name="api"),
]