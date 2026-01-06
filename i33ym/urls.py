from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("tinymce/", include("tinymce.urls")),
    path("react/", include("apps.reactions.urls")),
    path("newsletter/", include("apps.subscribers.urls")),
    path("rag/", include("apps.rag.urls")),
    
    path("workshops/", TemplateView.as_view(template_name="workshops.html"), name="workshops"),
    path("slides/", TemplateView.as_view(template_name="slides-rag.html"), name="slides"),
    path("slides-rag/", TemplateView.as_view(template_name="slides-rag.html"), name="slides-rag"),
    path("slides-perceptron/", TemplateView.as_view(template_name="slides-perceptron.html"), name="slides-perceptron"),
    path("demo-perceptron/", TemplateView.as_view(template_name="demo-perceptron.html"), name="demo-perceptron"),
    
    path("", include("apps.articles.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)