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
    path("demo-adaline/", TemplateView.as_view(template_name="demo-adaline.html"), name="demo-adaline"),
    path("slides-adaline/", TemplateView.as_view(template_name="slides-adaline.html"), name="slides-adaline"),
    path("demo-backpropogation/", TemplateView.as_view(template_name="demo-backpropogation.html"), name="demo-backpropogation"),
    path("demo-nats-core/", TemplateView.as_view(template_name="demo-nats-core.html"), name="demo-nats-core"),
    path("demo-nats-jetstream/", TemplateView.as_view(template_name="demo-nats-jetstream.html"), name="demo-nats-jetstream"),
    path("demo-nats-advanced/", TemplateView.as_view(template_name="demo-nats-advanced.html"), name="demo-nats-advanced"),
    path("demo-nats-production/", TemplateView.as_view(template_name="demo-nats-production.html"), name="demo-nats-production"),
    path("slides-backpropogation/", TemplateView.as_view(template_name="slides-backpropogation.html"), name="slides-backpropogation"),
    path("slides-nats-core/", TemplateView.as_view(template_name="slides-nats-core.html"), name="slides-nats-core"),
    path("slides-nats-jetstream/", TemplateView.as_view(template_name="slides-nats-jetstream.html"), name="slides-nats-jetstream"),
    path("slides-nats-advanced/", TemplateView.as_view(template_name="slides-nats-advanced.html"), name="slides-nats-advanced"),
    path("slides-nats-production/", TemplateView.as_view(template_name="slides-nats-production.html"), name="slides-nats-production"),
    path("slides-security/", TemplateView.as_view(template_name="slides-security.html"), name="slides-security"),
    path("", include("apps.articles.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)