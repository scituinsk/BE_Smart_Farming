from rest_framework import serializers
from .models import *

class AlarmSerializer(serializers.ModelSerializer):

    class Meta:
        model = Alarm
        fields = [
            'id', 'modul', 'label','duration', 'time', 'is_active',
            'repeat_monday', 'repeat_tuesday', 'repeat_wednesday',
            'repeat_thursday', 'repeat_friday', 'repeat_saturday', 'repeat_sunday',
            'created_at', 'updated_at'
        ]

class ScheduleLogSerializer(serializers.ModelSerializer):
    modul = serializers.SlugRelatedField(read_only=True,slug_field='name')
    class Meta:
        model = ScheduleLog
        fields = ['id','modul', 'message', 'created_at']