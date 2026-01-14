from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from smartfarming.tasks import task_send_push_notification

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    description = models.CharField(max_length=255, null=True, blank=True)
    image = models.FileField(upload_to='profiles/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}"
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """ 
    Membuat objek UserProfile setiap kali User baru disimpan
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(pre_save, sender=UserProfile)
def delete_old_profile_image_on_update(sender, instance, **kwargs):
    """
    Hapus gambar setiap user update foto profile baru
    """
    if not instance.pk:
        return
    try:
        old_instance = UserProfile.objects.get(pk=instance.pk)
    except UserProfile.DoesNotExist:
        return
    old_image = old_instance.image
    if old_image and old_image != instance.image and old_image.storage.exists(old_image.name):
        old_image.delete(save=False)

class NotificationType(models.TextChoices):
    SCHEDULE = "schedule", "Schedule"
    SYSTEM = "system", "System"
    MODULE = "module", "Module"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=20, choices=NotificationType.choices, default=NotificationType.SYSTEM, blank=True, null=True,)
    title = models.CharField(max_length=100, blank=True, null=True)  # jika schedule → nama grup penjadwalan
    body = models.CharField(max_length=255, blank=True, null=True)  # isi pesan singkat
    read = models.BooleanField(default=False)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def create_notification_user(cls, *, user, type: NotificationType = NotificationType.SYSTEM, title: str | None = None, body: str | None = None, data: dict | None = None, send_push: bool = True,):
        """
        Membuat dan mengirim notifikasi untuk 1 user
        """
        task_send_push_notification.delay(user_id=user.id, title=title, body=body, data=data or {})
        return cls.objects.create(user=user, type=type, title=title, body=body, data=data or {})
    
    @classmethod
    def bulk_create_for_users(cls, users, notif_type=NotificationType.SYSTEM, title=None, body=None, data=None, exclude_user_id=None, ):
        if data is None:
            data = {}

        notifications = []
        for user in users:
            if exclude_user_id and user.id == exclude_user_id:
                continue

            notifications.append(cls( user=user, type=notif_type, title=title, body=body, data=data)
            )

        if notifications:
            cls.objects.bulk_create(notifications)

        return notifications


    @classmethod
    def mark_as_read(cls, id, user):
        notif = cls.objects.get(id=id, user=user)
        notif.read = True
        notif.save(update_fields=["read"])
        return notif

    
    @classmethod
    def mark_all_as_read(cls, user):
        qs = cls.objects.filter(user=user, read=False)
        qs.update(read=True)
        return qs



    def __str__(self):
        return f"{self.type} - {self.title}"