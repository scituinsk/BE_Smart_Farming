from rest_framework import serializers
from .models import UserProfile
from schedule.models import Alarm


class ProfileSerializers(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    modul_count = serializers.SerializerMethodField()
    penjadwalan_count = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'first_name', 'last_name', 'description', 'image', 'modul_count', 'penjadwalan_count'
        ]

    def get_modul_count(self, obj):
        return obj.user.modul_set.count()

    def get_penjadwalan_count(self, obj):
        # hitung semua alarm dari seluruh modul yang dimiliki user
        return Alarm.objects.filter(modul__user=obj.user).count()
