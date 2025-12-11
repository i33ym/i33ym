from django.urls import path
from . import views

app_name = "articles"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("tag/<slug:slug>/", views.articles_by_tag, name="by_tag"),
    path("<slug:slug>/", views.article_detail, name="detail"),
    path("<slug:slug>/comment/", views.add_comment, name="add_comment"),
]