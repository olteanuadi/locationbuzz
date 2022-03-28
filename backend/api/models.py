from django.db import models
from django.db.models.fields import CharField
from django.contrib.postgres.fields import ArrayField 

# Create your models here.
class Location(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=300)
    unique_code = models.CharField(max_length=8, unique=True, default=None)
    image = models.ImageField(upload_to="images/{}".format(unique_code))
    rating = models.IntegerField()
    web_site = models.CharField(max_length=40, null=True)
    contact_phone = models.CharField(max_length=15, null=True)

    # Characteristics of the location
    characteristics = ArrayField(
        base_field=CharField(max_length=20)
        )
    
    type_of_location = ArrayField(
        base_field=CharField(max_length=20)
        )

    city = models.CharField(max_length=30)
    country = models.CharField(max_length=30)
    address = models.CharField(max_length=100)
    minimum_num_people = models.IntegerField()
    reservation_recommended = models.BooleanField(default=False)

    def __str__(self):
        return self.name
