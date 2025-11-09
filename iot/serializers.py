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
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        new_password = validated_data.get('password', None)

        # bersihkan user lain jika password diubah
        if new_password and instance.password != new_password:
            users_to_remove = instance.user.exclude(id=request.user.id)
            instance.user.remove(*users_to_remove)

        return super().update(instance, validated_data)

class ModulePinSerializers(serializers.ModelSerializer):
    
    class Meta:
        model = ModulePin
        fields = ['id', 'module', 'group', 'name', 'pin']
        read_only_fields = ['module']

    def validate(self, attrs):
        """
        Cegah duplikasi pin dalam modul yang sama
        """
        module = self.context.get('module')
        if not module:
            module = attrs.get('module')
        pin = attrs.get('pin')
        if module and ModulePin.objects.filter(module=module, pin=pin).exists():
            raise serializers.ValidationError(f"Pin {pin} sudah digunakan pada modul {module.serial_id}.")
        if int(pin) <= 0:
            raise serializers.ValidationError(f"Nilai pin harus lebih dari 0 pin saat ini {pin}")
        return attrs

    def update(self, instance, validated_data):
        request = self.context.get('request')

        # Hanya admin yang boleh melakukan perubahan field terrtentu
        if request and not request.user.is_staff:
            if 'module' in validated_data:
                validated_data.pop('module')
            if 'pin' in validated_data:
                validated_data.pop('pin')
        return super().update(instance, validated_data)

class contoh(serializers.ModelSerializer):
    
    class Meta:
        model = Modul
        fields = []
        read_only_fields = []