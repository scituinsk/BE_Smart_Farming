from rest_framework import serializers
from .models import *
from profil.models import *
from smartfarming.tasks import task_broadcast_module_notification
from django.utils import timezone

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
        features_queryset = modul_obj.feature.all()
        datamodul_map = {
            (dm.feature_id): dm.data
            for dm in DataModul.objects
                .filter(modul=modul_obj)
                .order_by('feature', '-last_data')
                .distinct('feature')
        }

        result_list = []
        for feature_obj in features_queryset:
            result_list.append({
                'name': feature_obj.name,
                'descriptions': feature_obj.descriptions,
                'data': datamodul_map.get(feature_obj.id)
            })
        return result_list

    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        new_password = validated_data.get('password', None)
        title = f"Password {instance.name} diubah!"
        body = f"User {request.user.email} mengubah password modul IoT"
        log_data = {
            "username": request.user.username,
            "email": request.user.email,
            "modul": str(instance.serial_id),
            "timestamp": timezone.now().isoformat().replace("+00:00", "Z"),
        }

        # bersihkan user lain jika password diubah
        if new_password and instance.password != new_password:
            users_before_change = instance.user.all()
            users_to_remove = instance.user.exclude(id=request.user.id)
            task_broadcast_module_notification.delay(modul_id=instance.id, title=title, body=body, data=log_data)
            Notification.bulk_create_for_users(users=users_before_change, notif_type=NotificationType.MODULE, title=title, body=body, data=log_data)
            instance.user.remove(*users_to_remove)

        return super().update(instance, validated_data)
    
    def get_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")

class ModulePinSerializers(serializers.ModelSerializer):
    class Meta:
        model = ModulePin
        fields = ['id', 'module', 'group', 'name', 'type','descriptions','status', 'pin']
        read_only_fields = ['module']

    def validate_pin(self, value):
        """
        Pastikan nilai pin valid (> 0)
        """
        if value <= 0:
            raise serializers.ValidationError(f"Nilai pin harus lebih dari 0. Pin saat ini: {value}")
        return value

    def validate(self, attrs):
        """
        Validasi untuk mencegah duplikasi pin per modul.
        Aman untuk CREATE dan UPDATE.
        """
        # ambil pin baru dari attrs
        pin = attrs.get('pin')

        # jika tidak ada perubahan pin (misalnya PATCH tanpa field ini), skip
        if pin is None:
            return attrs

        # ambil module dari context, instance, atau data input
        module = (
            self.context.get('module') or
            getattr(self.instance, 'module', None) or
            attrs.get('module')
        )

        if not module:
            raise serializers.ValidationError({"detail": "Konteks 'module' tidak ditemukan."})

        # hanya cek ke DB jika create atau pin berubah
        if not self.instance or (self.instance and pin != self.instance.pin):
            qs = ModulePin.objects.filter(module=module, pin=pin)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                # ambil nama atau serial_id modul untuk pesan error
                module_name = getattr(module, 'serial_id', None) or getattr(module, 'name', None) or str(module)
                raise serializers.ValidationError(f"Pin {pin} sudah digunakan pada modul {module_name}.")

        return attrs

    def update(self, instance, validated_data):
        """
        Batasi perubahan field tertentu untuk non-admin user.
        """
        request = self.context.get('request')

        # jika tidak ada request atau bukan staff, user tidak boleh ubah pin
        if not (request and hasattr(request, 'user') and request.user.is_staff):
            validated_data.pop('pin', None)

        return super().update(instance, validated_data)
    
class ModuleLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleLog
        fields = ['id', 'module', 'schedule', 'type', 'name', 'alarm_at', 'data', 'updated_at', 'created_at']
    
    def get_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")