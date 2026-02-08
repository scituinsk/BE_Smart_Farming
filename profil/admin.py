from django.contrib import admin
from profil.models import *
from smartfarming.models import Contact, Terms, FirmwareUpdate

# Register your models here.

admin.site.register(UserProfile)
admin.site.register(Notification)
admin.site.register(Contact)
admin.site.register(Terms)

@admin.register(FirmwareUpdate)
class FirmwareUpdateAdmin(admin.ModelAdmin):
    list_display = ('version', 'is_active', 'created_at', 'file_size')
    list_filter = ('is_active',)
    search_fields = ('version',)

    def file_size(self, obj):
        if obj.file:
            return f"{obj.file.size / 1024:.2f} KB"
        return "0 KB"

admin.site.site_header = "SCIT Admin"
admin.site.site_title = "SCIT Admin Portal"
admin.site.index_title = "Dashboard SCIT"