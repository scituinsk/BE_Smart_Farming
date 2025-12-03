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
        fields = ['id', 'modul', 'name', 'sequential', 'pins']

    def get_pins(self, obj):
        """
        Mengambil semua pin yang terkait dengan GroupSchedule ini melalui relasi ModulePin yang punya field 'group' = obj.
        """
        pins = ModulePin.objects.filter(group=obj)
        return [{'name': p.name, 'pin': p.pin, 'status': p.status} for p in pins]
    
    # grup tidak boleh pindah modul 
    def update(self, instance, validated_data):
        request = self.context.get('request')
        sequential = validated_data.get('sequential')
        pins = ModulePin.objects.filter(group=instance).count()

        if sequential != None and sequential > pins:
            raise serializers.ValidationError(f"Nilai {sequential} melebihi jumlah pin yang ada {pins}")

        # Hanya admin yang boleh melakukan perubahan field terrtentu
        if request and not request.user.is_staff:
            if 'modul' in validated_data:
                validated_data.pop('modul', None)
        return super().update(instance, validated_data)