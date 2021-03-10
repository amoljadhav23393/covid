from django.db import models
from django.contrib.auth.models import User

country = models.CharField(max_length=50,blank=True,null=True)
country.contribute_to_class(User,'country')