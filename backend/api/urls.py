from django.urls import path
from . import views

urlpatterns = [
    path('', views.Index.as_view(), name="index"),
    path('find/', views.ProcessFormData.as_view(), name="process_form_data")
]