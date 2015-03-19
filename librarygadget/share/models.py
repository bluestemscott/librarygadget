from django.db import models
from django.utils.encoding import force_unicode

class ShareEvent(models.Model):
	linktitle = models.CharField(max_length=300)	
	linkurl = models.URLField(max_length=500)
	SHARE_SYSTEMS = (
		('facebook', 'Facebook'),
		('twitter', 'Twitter')
	)
	sharesystem = models.CharField(max_length=20, choices=SHARE_SYSTEMS)
	lastmodified = models.DateField(auto_now=True)

