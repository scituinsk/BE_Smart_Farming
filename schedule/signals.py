from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from smartfarming.celery import app as celery_app
from smartfarming.utils.schedule import schedule_alarm_task
from .models import Alarm

@receiver(post_save, sender=Alarm)
def schedule_or_update_alarm(sender, instance, **kwargs):
    """Dipicu setiap kali objek Alarm disimpan."""
    # Batalkan tugas Celery lama jika ada
    if instance.celery_task_id:
        celery_app.control.revoke(instance.celery_task_id)

    # Jika alarm aktif, jadwalkan tugas baru
    if instance.is_active:
        schedule_alarm_task(instance)
    else:
        # Jika alarm dinonaktifkan, hapus ID tugasnya
        Alarm.objects.filter(pk=instance.pk).update(celery_task_id=None)

@receiver(post_delete, sender=Alarm)
def cancel_alarm_task_on_delete(sender, instance, **kwargs):
    """Dipicu setiap kali objek Alarm dihapus."""
    if instance.celery_task_id:
        celery_app.control.revoke(instance.celery_task_id)