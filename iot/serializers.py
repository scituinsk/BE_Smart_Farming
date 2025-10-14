from rest_framework import serializers
from .models import *

class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username','email', 'first_name', 'last_name']

class FeatureSerializers(serializers.ModelSerializer):
    
    class Meta:
        model = Feature
        fields = '__all__'

class ModulSerializers(serializers.ModelSerializer):
    user = UserSerializers(many=True, read_only=True)
    feature = FeatureSerializers(many=True, read_only=True)
    
    class Meta:
        model = Modul
        fields = ['id','type','user', 'serial_id','auth_id', 'name', 'descriptions','image', 'feature','password', 'created_at']
        read_only_fields = ['serial_id','auth_id', 'feature', 'created_at']

# class DataModulSerializers(serializers.ModelSerializer):
#     modul = serializers.SlugRelatedField(read_only=True,slug_field='name')
#     feature = serializers.SlugRelatedField(read_only=True,slug_field='name')
    
#     class Meta:
#         model = DataModul
#         fields = ['modul', 'feature', 'data', 'last_data']
#         read_only_fields = ['data', 'last_data']

class contoh(serializers.ModelSerializer):
    
    class Meta:
        model = Modul
        fields = []
        read_only_fields = []