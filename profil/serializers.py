from rest_framework import serializers
from profil.models import *
from schedule.models import Alarm

class UserRoleSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = ['id', 'username', 'email'] 

    def get_role(self, obj):
        # Jika is_staff True -> "admin", selain itu "user"
        return "admin" if obj.is_staff else "user"

class ProfileSerializers(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    modul_count = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'user_id', 'username', 'email', 'first_name', 'last_name', 'description', 'image', 'modul_count'
        ]

    def get_modul_count(self, obj):
        return obj.user.modul_set.count()
    
    def update(self, instance, validated_data):
        # ambil data untuk model User jika ada
        user_data = validated_data.pop('user', {})
        user = instance.user

        # update field first_name dan last_name pada objek user
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.save()
        instance = super().update(instance, validated_data)
        
        return instance
    
class NotificationSerializers(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
