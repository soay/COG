from django.db import models
from constants import APPLICATION_LABEL
from django.contrib.auth.models import User
from communication_means import CommunicationMeans

class CommunicationMeansMember(models.Model):  
    
    user = models.ForeignKey(User, blank=False, null=False)
    communicationMeans = models.ForeignKey(CommunicationMeans, blank=False, null=False)
            
    class Meta:
        unique_together = (("user", "communicationMeans"),)
        app_label= APPLICATION_LABEL
