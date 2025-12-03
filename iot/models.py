from django.db import models
from django.contrib.auth.models import User
from uuid6 import uuid7

# Create your models here.

class Modul(models.Model):
    """ Model untuk menyimpan data microcontroller dan generate uuid baru jika uuid bocor """
    serial_id = models.UUIDField(default=uuid7) # menggunakann uuid7 untuk fleksibilitas kedepanya
    auth_id = models.UUIDField(default=uuid7) 
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

class DataModul(models.Model):
    """ Model untuk menyimpan data terakhir dari modul menurut featurenya """
    modul = models.ForeignKey(Modul, on_delete=models.CASCADE, related_name='data')
    feature = models.ForeignKey('Feature', on_delete=models.CASCADE, related_name='data')
    data = models.JSONField(blank=True, null=True)
    last_data = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.modul.name} - {self.feature.name}"

# class DetailDataModul(models.Model):
#     """ Model untuk menyimpan detail data terakhir dari modul menurut featurenya """
#     data_modul = models.ForeignKey(DataModul, on_delete=models.CASCADE, related_name='detail_data_modul')
#     name = models.CharField(max_length=255, blank=True, null=True)
#     data = models.CharField(max_length=255, blank=True, null=True)
#     last_data = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.name} - {self.data_modul}"

class Feature(models.Model):
    """ Model feature yang hanya dapat dimodifikasi oleh admin """
    name = models.CharField(max_length=50)
    descriptions = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"

class ModulePin(models.Model):
    module = models.ForeignKey(Modul, on_delete=models.CASCADE, related_name='pins')
    group = models.ForeignKey('schedule.GroupSchedule', on_delete=models.SET_NULL, null=True, blank=True, related_name='pins')
    name = models.CharField(max_length=20, blank=True, null=True)
    type = models.CharField(max_length=20, blank=True, null=True)
    descriptions = models.CharField(max_length=50, blank=True, null=True)
    status = models.BooleanField(default=False)
    pin = models.IntegerField(default=0)

    def set_off(self):
        self.status = False
        self.save(update_fields=['status'])
    
    def set_on(self):
        self.status = True
        self.save(update_fields=['status'])

    def __str__(self):
        return f"{self.module.serial_id} - {self.pin}"
    

# class ModuleLog(models.Model):
#     module = models.ForeignKey(Modul, on_delete=models.CASCADE, related_name='pins')
#     type = models.CharField(max_length=20, blank=True, null=True) # dari schedule atau modul?
#     name = models.CharField(max_length=20, blank=True, null=True) # if schedule = nama grup penjadwalan
