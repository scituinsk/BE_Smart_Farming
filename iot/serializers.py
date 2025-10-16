from rest_framework import serializers
from .models import *

class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username','email', 'first_name', 'last_name']

class DataModulSerializers(serializers.ModelSerializer):
    modul = serializers.SlugRelatedField(read_only=True,slug_field='name')
    feature = serializers.SlugRelatedField(read_only=True,slug_field='name')
    
    class Meta:
        model = DataModul
        fields = ['modul', 'feature', 'data', 'last_data']
        read_only_fields = ['data', 'last_data']

class FeatureSerializers(serializers.ModelSerializer):
    data = DataModulSerializers(many=True, read_only=True, source='data')
    
    class Meta:
        model = Feature
        fields = ['name', 'descriptions', 'data']

class ModulSerializers(serializers.ModelSerializer):
    user = UserSerializers(many=True, read_only=True)
    feature = serializers.SerializerMethodField()
    
    class Meta:
        model = Modul
        fields = ['id','type','user', 'serial_id','auth_id', 'name', 'descriptions','image', 'feature','password', 'created_at']
        read_only_fields = ['serial_id','auth_id', 'created_at']

    def get_feature(self, modul_obj):
        """
        Method ini membuat list 'feature' secara dinamis, 
        menyisipkan nilai 'data' terakhir untuk setiap feature.
        """
        # Dapatkan semua feature yang terhubung dengan modul ini
        features_queryset = modul_obj.feature.all()
        result_list = []

        for feature_obj in features_queryset:
            data_value = None
            try:
                # Cari data terakhir di DataModul yang cocok dengan modul DAN feature saat ini
                latest_data = DataModul.objects.filter(
                    modul=modul_obj, 
                    feature=feature_obj
                ).latest('last_data')
                data_value = latest_data.data
            except DataModul.DoesNotExist:
                pass

            feature_data = {
                'name': feature_obj.name,
                'descriptions': feature_obj.descriptions,
                'data': data_value
            }
            result_list.append(feature_data)
            
        return result_list

class contoh(serializers.ModelSerializer):
    
    class Meta:
        model = Modul
        fields = []
        read_only_fields = []