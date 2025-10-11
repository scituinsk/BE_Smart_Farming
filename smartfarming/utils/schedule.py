from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from schedule.models import Alarm
from schedule.tasks import trigger_alarm_task

# Kamus ini sekarang ada di sini
WEEKDAYS = {
    0: 'repeat_monday', 1: 'repeat_tuesday', 2: 'repeat_wednesday',
    3: 'repeat_thursday', 4: 'repeat_friday', 5: 'repeat_saturday',
    6: 'repeat_sunday',
}

def get_next_run_datetime(alarm):
    """Menghitung datetime absolut berikutnya kapan alarm harus berbunyi."""
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    alarm_time = alarm.time
    run_datetime = now.replace(
        hour=alarm_time.hour, minute=alarm_time.minute,
        second=alarm_time.second, microsecond=0
    )

    if not alarm.is_repeating:
        if run_datetime <= now:
            run_datetime += timedelta(days=1)
        return run_datetime

    # Cari hari pengulangan berikutnya, mulai dari HARI INI
    for i in range(7):
        next_day_offset = (now.weekday() + i) % 7
        if getattr(alarm, WEEKDAYS[next_day_offset]):
            potential_run = run_datetime + timedelta(days=i)
            if potential_run > now:
                return potential_run

    # Jika tidak ditemukan (misal waktu hari ini sudah lewat), cari mulai dari MINGGU DEPAN
    for i in range(7):
        next_day_offset = (now.weekday() + i) % 7
        if getattr(alarm, WEEKDAYS[next_day_offset]):
            return run_datetime + timedelta(days=i+7)
            
    return None

def schedule_alarm_task(alarm):
    """
    Fungsi utama untuk menjadwalkan satu tugas alarm.
    Ini akan menghitung waktu berikutnya dan membuat tugas Celery.
    """
    next_run = get_next_run_datetime(alarm)
    
    if next_run:
        task = trigger_alarm_task.apply_async(
            args=[alarm.id],
            eta=next_run
        )
        # Simpan ID tugas baru ke model
        Alarm.objects.filter(pk=alarm.pk).update(celery_task_id=task.id)
        print(f"SCHEDULER: Alarm {alarm.id} dijadwalkan dengan tugas {task.id} pada {next_run.strftime('%Y-%m-%d %H:%M:%S')}")