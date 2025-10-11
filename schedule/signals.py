from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo 

from .models import Alarm
from .tasks import trigger_alarm_task
from smartfarming.celery import app as celery_app

# Kamus untuk memetakan nama hari ke atribut model
WEEKDAYS = {
    0: 'repeat_monday',
    1: 'repeat_tuesday',
    2: 'repeat_wednesday',
    3: 'repeat_thursday',
    4: 'repeat_friday',
    5: 'repeat_saturday',
    6: 'repeat_sunday',
}

def get_next_run_datetime(alarm):
    """
    Menghitung datetime absolut berikutnya kapan alarm harus berbunyi,
    berdasarkan waktu saat ini, waktu alarm, dan hari pengulangan.
    """
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    alarm_time = alarm.time
    
    # Gabungkan tanggal hari ini dengan waktu alarm
    run_datetime = now.replace(
        hour=alarm_time.hour, minute=alarm_time.minute,
        second=alarm_time.second, microsecond=0
    )

    # Jika tidak berulang, dan waktu sudah lewat untuk hari ini, jadwalkan untuk besok
    if not alarm.is_repeating:
        if run_datetime <= now:
            run_datetime += timedelta(days=1)
        return run_datetime

    # Jika berulang, cari hari aktif berikutnya
    for i in range(7):
        next_day_offset = (now.weekday() + i) % 7
        is_repeat_day = getattr(alarm, WEEKDAYS[next_day_offset])

        if is_repeat_day:
            # Jika hari ini adalah hari pengulangan dan waktu belum lewat
            if i == 0 and run_datetime > now:
                return run_datetime
            # Jika tidak, cari di hari pengulangan berikutnya
            elif i > 0:
                return run_datetime + timedelta(days=i)

    # Jika hari ini adalah hari pengulangan tapi waktu sudah lewat,
    # cari hari pengulangan berikutnya mulai dari besok
    for i in range(1, 8):
        next_day_offset = (now.weekday() + i) % 7
        if getattr(alarm, WEEKDAYS[next_day_offset]):
            return run_datetime + timedelta(days=i)

    return None

@receiver(post_save, sender=Alarm)
def schedule_or_update_alarm(sender, instance, **kwargs):
    """
    Dipicu setiap kali objek Alarm disimpan (dibuat atau diperbarui).
    """
    # Batalkan tugas Celery lama jika ada
    if instance.celery_task_id:
        celery_app.control.revoke(instance.celery_task_id)
        print(f"SIGNAL: Tugas lama {instance.celery_task_id} untuk Alarm {instance.id} dibatalkan.")

    # Jika alarm aktif, jadwalkan tugas baru
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    if instance.is_active:
        next_run = get_next_run_datetime(instance)
        print("="*40)
        print(f"SIGNAL DEBUG: Menjadwalkan Alarm ID: {instance.id}")
        print(f"SIGNAL DEBUG: Waktu saat ini (timezone aware): {now}")
        print(f"SIGNAL DEBUG: Waktu alarm dari DB: {instance.time}")
        print(f"SIGNAL DEBUG: Waktu eksekusi berikutnya dihitung: {next_run}")
        print("="*40)
        
        if next_run:
            # Jadwalkan tugas baru untuk dijalankan pada waktu yang dihitung
            task = trigger_alarm_task.apply_async(
                args=[
                    instance.modul.serial_id,
                    instance.id,
                    instance.label,
                    instance.time.strftime('%H:%M:%S')
                ],
                eta=next_run  # Estimated Time of Arrival (ETA)
            )
            
            # Simpan ID tugas baru ke model (tanpa memicu sinyal lagi)
            Alarm.objects.filter(pk=instance.pk).update(celery_task_id=task.id)
            print(f"SIGNAL: Alarm {instance.id} dijadwalkan dengan tugas baru {task.id} pada {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        # Jika alarm dinonaktifkan, pastikan tidak ada ID tugas yang tersimpan
        Alarm.objects.filter(pk=instance.pk).update(celery_task_id=None)

@receiver(post_delete, sender=Alarm)
def cancel_alarm_task_on_delete(sender, instance, **kwargs):
    """
    Dipicu setiap kali objek Alarm dihapus.
    """
    if instance.celery_task_id:
        celery_app.control.revoke(instance.celery_task_id)
        print(f"SIGNAL: Alarm {instance.id} dihapus, tugas {instance.celery_task_id} dibatalkan.")