from django.db import models
from django.contrib.auth.models import User
from uuid6 import uuid7

# Create your models here.

class Modul(models.Model):
    """ Model untuk menyimpan data microcontroller dan generate uuid baru jika uuid bocor """
    serial_id = models.UUIDField(default=uuid7) # menggunakann uuid7 untuk fleksibilitas kedepanya
    type  = models.CharField(max_length=50)
    user = models.ManyToManyField(User, blank=True)
    password = models.CharField(max_length=10, default="paktani")
    name = models.CharField(max_length=50, blank=True, null=True)
    descriptions = models.CharField(max_length=255, blank=True, null=True)
    image = models.FileField()
    status = models.BooleanField(default=False)
    feature = models.ManyToManyField('Feature')
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_new_uuid(self):
        self.serial_id = uuid7()
        self.save(update_fields=['serial_id'])

    def __str__(self):
        return f"{self.name} - {self.serial_id}"

# class DataModul(models.Model):
#     """ Model untuk menyimpan data terakhir dari modul menurut featurenya """
#     modul = models.ForeignKey(Modul, name='data_modul', on_delete=models.CASCADE)
#     feature = models.ForeignKey('Feature', name='data_feature_modul', on_delete=models.CASCADE)
#     data = models.CharField(max_length=255, blank=True, null=True)
#     last_data = models.DateTimeField(auto_now=True)

class Feature(models.Model):
    """ Model feature yang hanya dapat dimodifikasi oleh admin """
    name = models.CharField(max_length=50)
    descriptions = models.CharField(max_length=255)
