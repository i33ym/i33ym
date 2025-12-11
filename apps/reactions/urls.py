from django.urls import path
from . import views

app_name = "reactions"

urlpatterns = [
    path("<slug:slug>/<str:reaction_type>/", views.toggle_reaction, name="toggle"),
]