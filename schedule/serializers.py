from rest_framework import serializers
from .models import *

class AlarmSerializer(serializers.ModelSerializer):

    class Meta:
        model = Alarm
        fields = [
            'id', 'group', 'label','duration', 'time', 'is_active',
            'repeat_monday', 'repeat_tuesday', 'repeat_wednesday',
            'repeat_thursday', 'repeat_friday', 'repeat_saturday', 'repeat_sunday',
            'created_at', 'updated_at'
        ]

class ScheduleLogSerializer(serializers.ModelSerializer):
    modul = serializers.SlugRelatedField(read_only=True,slug_field='name')
    class Meta:
        model = ScheduleLog
        fields = ['id','modul', 'message', 'created_at']

class GroupScheduleSerializer(serializers.ModelSerializer):
    pins = serializers.SerializerMethodField()

    class Meta:
        model = GroupSchedule
        fields = ['id', 'modul', 'name', 'pins']

    def get_pins(self, obj):
        """
        Mengambil semua pin yang terkait dengan GroupSchedule ini melalui relasi ModulePin yang punya field 'group' = obj.
        """
        pins = ModulePin.objects.filter(group=obj)
        return [{'name': p.name, 'pin': p.pin} for p in pins]