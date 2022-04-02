from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('', views.Index.as_view(), name="index"),
    path('find/', views.ProcessFormData.as_view(), name="process_form_data"),
    path('results/', TemplateView.as_view(template_name="index/results.html"), name="results"),
]