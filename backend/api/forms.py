from django import forms

class SearchForm(forms.Form):
    relaxing_range = forms.CharField()
    loudness_range = forms.CharField()
    restaurant = forms.CharField()
    cafe = forms.CharField()
    park = forms.CharField()


