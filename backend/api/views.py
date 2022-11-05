from os import environ
from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.template.response import TemplateResponse
from requests.api import request
# from django.contrib.gis.utils import GeoIP
from .forms import SearchForm
import json
import random
import requests
import environ

from google_images_search import GoogleImagesSearch

env = environ.Env()
environ.Env.read_env()

# Create your views here.
class Index(View):
    def get(self, *args, **kwargs):
        with open("api/categories.json", "r") as file:
            file_text = file.read()
            categories = json.loads(file_text)

        return TemplateResponse(self.request, template="index/index.html", context={"categories":categories.keys})


class ProcessFormData(View):
    def relaxing_scale(self, reviews) -> int:
        '''Return a number from 0 to 100 representing the relaxing scale
        of the location. 0 is the most relaxing, 100 is the most engaging and
        loud.
        
        'reviews' holds a json as a string containing location reviews.
        '''
        with open('api/key_words.json', 'r') as file:
            file_txt = file.read()
            key_words = json.loads(file_txt)
        
        words = []
        words_no = 0
        scales_sum = 0
        reviews = json.loads(reviews)
        # Putting every review in a list
        reviews = [review['text'] for review in reviews]
        # Averaging the mood of the place by iterating through each word in the review
        # and checking it with the key words in 'key_words.json'
        for review in reviews:
            review = review.lower().replace('.', ' ').replace(',', ' ').replace('  ', ' ')
            words = review.split(' ')
            for word in words:
                # 'scale' is the "relaxing scale" that word is at
                # and 'k_words' is a list containing all the words
                # at that scale
                for scale, k_words in key_words.items():
                    if word in k_words:
                        words_no += 1
                        scales_sum += int(scale)
        try:
            return (scales_sum / words_no)
        except Exception:
            return 50


    def get_categ_id(self, keys: list) -> list:
        '''Return FSQ Category IDs from given keywords.
        
        Parameters :
        keys (list) : category keywords (e.g. "Park")
        '''
        categ_ids = []
        with open(r"api/categories.json", "r") as file:
            categ = json.loads(file.read())
        for key, id in categ.items():
            if key in keys:
                categ_ids.append(id)

        # Randomising elements' order
        random.shuffle(categ_ids)
        return categ_ids


    def post(self, *args, **kwargs):
        # Retrieving form data
        criteria = self.request.POST.getlist('crit')
        user_relaxing = int(self.request.POST['relaxing_range'])
        location = self.request.POST['location']
        # Storing future category ids in list 'categ_id' 
        categ_id = []
        # Loading 'categories.json' and storing its content in 'content'
        content = {}
        with open(r"api/categories.json", "r") as file:
            content = file.read()
            content = json.loads(content)
        # 'requested_criteria' holds a boolean value which is True in case the user
        # has inputed special criteria
        requested_criteria = False
        # Number of returned locations
        venues_limit = 0
        if not criteria and user_relaxing == 50:
            categories = [
                "Cafe",
                "Restaurant",
                "Landmarks and Outdoors",
                "Arts and Entertainment"
            ]
            # Retrieving 2 locations per category from 'categories'
            categ_id = self.get_categ_id(categories)
            venues_limit = 2
        else:
            # Retrieving the category ids associated with the user's input
            for crit in criteria:
                if crit in content.keys():
                    categ_id.append(content[crit])
            requested_criteria = True
            venues_limit = 20

        # Creating list 'coords' containing user's latitude and longitude
        coords = location.split('/')
        # If the user has inputed categories, choosing one for url
        urls = f"{env('FQ_URL')}ll={coords[0]}%2C{coords[1]}&radius=10000&categories={categ_id[0]}&limit={venues_limit}"
        if not requested_criteria:
            # If user hasn't inputed categories, creating a url for every categ.
            urls = [f"{env('FQ_URL')}ll={coords[0]}%2C{coords[1]}&radius=10000&categories={category}&limit={venues_limit}" for category in categ_id]
        # Setting up the headers for the API request
        headers = {
            "Accept": "application/json",
            "Authorization": env("FQ_API_KEY"),
        }

        # Retrieving the response as a JSON
        outputs = {"results": []}
        if not requested_criteria:
            for url in urls:
                response = requests.request("GET", url, headers=headers)
                output = json.loads(response.text)
                outputs["results"].extend(output["results"])
        else:
                response = requests.request("GET", urls, headers=headers)
                outputs = json.loads(response.text)
        
        # Getting locations that only fit the relaxing criteria
        # and storing their fsq_id in 'in_crit_locations'
        in_crit_locations = []
        if requested_criteria:
            for result in outputs['results']:
                fsq_id = result["fsq_id"]

                # Retrieving reviews using Foresquare's API
                reviews_url = f"https://api.foursquare.com/v3/places/{fsq_id}/tips?limit=2&fields=text&sort=POPULAR"
                response = requests.request("GET", reviews_url, headers=headers)
                scale = self.relaxing_scale(response.text)
                # If the review average mood is almost equals to user's input
                # then store the id in 'in_crit_locations'
                if scale >= user_relaxing - 10 and scale <= user_relaxing + 10:
                    in_crit_locations.append(fsq_id)

        # Adding the details lists in list 'location_details'
        location_details = []
        for result in outputs['results']:
            fsq_id = result["fsq_id"]
            loc_name = result['name']
            loc_type = result['categories'][0]['name']
            loc_distance = result['distance'] // 1000
            try:
                loc_address = result['location']['address']
            except Exception:
                loc_address = 'No address found.'

            # In case the user has requested special criteria, get only
            # the locations that meet the criteria average
            if requested_criteria and fsq_id not in in_crit_locations:
                continue

            # Requesting the average price of the location and wether
            # it is open now or not
            details_url = f"https://api.foursquare.com/v3/places/{fsq_id}?fields=hours%2Cprice"
            details_request = requests.request("GET", url=details_url, headers=headers)
            details = json.loads(details_request.text)
            open_now = details['hours']['open_now']
            is_open_now = "Yes" if open_now else ("No" if open_now is False else "Unknown")
            try: 
                price = details["price"]
            except KeyError:
                price = "Unknown"

            # Using Google's API to search images
            # gis = GoogleImagesSearch(env('GOOGLE_KEY'), env('GOOGLE_CX'))
            # _search_params = {
            #     'q': loc_name,
            #     'num': 1,
            #     'fileType': 'jpg',
            #     'safe': 'active',
            # }
            # gis.search(search_params=_search_params)
            # loc_img_url = (gis.results())[0].url
            loc_img_url = r"https://www.freepnglogos.com/uploads/pin-png/location-pin-connectsafely-37.png"
            location_details.append([loc_name, loc_type, loc_distance, loc_address, loc_img_url, is_open_now, price])

        
        return TemplateResponse(self.request, 'index/results.html', context={'location_details': location_details})
