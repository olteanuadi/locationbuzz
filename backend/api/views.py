from django.shortcuts import render
from django.views import View
from django.template.response import TemplateResponse

# Create your views here.
class Index(View):

    def get(self, *args, **kwargs):
        return TemplateResponse(self.request, template="index/index.html")
