import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Alarm

@shared_task(name="trigger_alarm_task")
def trigger_alarm_task(alarm_id):
    """
    Tugas Celery yang HANYA dijalankan untuk membunyikan satu alarm.
    """
    try:
        alarm = Alarm.objects.get(pk=alarm_id)
    except Alarm.DoesNotExist:
        print(f"ALARM TASK: Alarm dengan ID {alarm_id} tidak ditemukan.")
        return

    # Kirim Pesan ke WebSocket
    channel_layer = get_channel_layer()
    group_name = f'grup_{alarm.modul.serial_id}'
    message_payload = {
        'type': 'alarm_triggered',
        'message': f"ALARM AKTIF: {alarm.label or 'Alarm'}"
    }
    
    print(f"ALARM TASK: Memicu alarm ID {alarm_id} untuk grup '{group_name}'")
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'channel.message',
            'message': json.dumps(message_payload),
            'sender_channel_name': 'celery_worker'
        }
    )

    if not alarm.is_repeating:
        alarm.is_active = False
        alarm.save(update_fields=['is_active'])
        print(f"ALARM TASK: Alarm sekali jalan ID {alarm_id} telah dinonaktifkan.")
        
    print(f"ALARM TASK: Selesai memicu alarm ID {alarm_id}.")


@shared_task(name="check_and_run_due_alarms")
def check_and_run_due_alarms():
    """
    Tugas pemeriksa yang dijalankan oleh Beat setiap menit.
    Tugas ini akan mencari semua alarm yang jatuh tempo 'sekarang'
    dan mengirimkannya ke worker.
    """
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    current_day_index = now.weekday()  # Senin=0, ..., Minggu=6
    
    # Ambil semua alarm yang aktif dan waktunya cocok dengan jam dan menit saat ini
    alarms_due_now = Alarm.objects.filter(
        is_active=True,
        time__hour=now.hour,
        time__minute=now.minute
    )

    print(f"BEAT CHECKER ({now.strftime('%H:%M')}): Menemukan {alarms_due_now.count()} alarm yang cocok dengan waktu.")

    for alarm in alarms_due_now:
        # Cek apakah alarm dijadwalkan untuk hari ini
        days_map = [
            alarm.repeat_monday, alarm.repeat_tuesday, alarm.repeat_wednesday,
            alarm.repeat_thursday, alarm.repeat_friday, alarm.repeat_saturday,
            alarm.repeat_sunday
        ]
        should_run_today = days_map[current_day_index]

        # Jika alarm ini seharusnya berulang tapi hari ini bukan jadwalnya, lewati.
        if alarm.is_repeating and not should_run_today:
            continue

        # Jika lolos dari pengecekan di atas, berarti alarm boleh dijalankan:
        # - Entah karena ini alarm sekali jalan (is_repeating = False)
        # - Entah karena ini alarm berulang dan hari ini adalah jadwalnya
        print(f"BEAT CHECKER: Mengirim tugas untuk Alarm ID {alarm.id} ke worker.")
        trigger_alarm_task.delay(alarm.id)