from os import environ
from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.template.response import TemplateResponse
# from django.contrib.gis.utils import GeoIP
from .forms import SearchForm
import json
import random
import requests
import environ

env = environ.Env()
environ.Env.read_env()

# Create your views here.
class Index(View):

    def get(self, *args, **kwargs):
        return TemplateResponse(self.request, template="index/index.html")


class ProcessFormData(View):
    def post(self, *args, **kwargs):
        # Retrieving form data
        criteria = self.request.POST.getlist('crit')
        relaxing = self.request.POST['relaxing_range']
        loudness = self.request.POST['loudness_range']
        location = self.request.POST['location']
        print(location)
        # Storing future category ids in list 'categ_id' 
        categ_id = []
        # Loading json 'categories.json' and storing its content in 'content'
        content = {}
        with open(r"api/categories.json", "r") as file:
            content = file.read()
            content = json.loads(content)
        if not criteria and int(relaxing) == 50 and int(loudness) == 50:
            # Retrieving a random number of categories in case the user hasn't selected any choice
            categ_id = random.choices([*content.values()], k=random.randint(1, len(content.values())))
        else:
            # Retrieving the category ids associated with the user's input
            for crit in criteria:
                if crit in content.keys():
                    categ_id.append(content[crit])

        # Formatting the ids to the correct url
        categ_str = "%2C".join(str(id) for id in categ_id)
        # Creating list 'coords' containing user's latitude and longitude
        coords = location.split('/')
        url = f"{env('FQ_URL')}ll={coords[0]}%2C{coords[1]}&radius=10000&categories={categ_str}"
        # Setting up the headers for the API request
        headers = {
            "Accept": "application/json",
            "Authorization": env("FQ_API_KEY"),
        }

        response = requests.request("GET", url, headers=headers)
        output = json.loads(response.text)
        print(output)
        return redirect('index')
