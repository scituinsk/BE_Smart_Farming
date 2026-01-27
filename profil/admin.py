from django.contrib import admin
from profil.models import *
from smartfarming.models import Contact

# Register your models here.

admin.site.register(UserProfile)
admin.site.register(Notification)
admin.site.register(Contact)

admin.site.site_header = "SCIT Admin"
admin.site.site_title = "SCIT Admin Portal"
admin.site.index_title = "Dashboard SCIT"