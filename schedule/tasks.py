import json
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Alarm

@shared_task(name="trigger_alarm_task")
def trigger_alarm_task(alarm_id):
    """
    Tugas Celery yang dijalankan saat alarm berbunyi.
    Tugas ini akan:
    1. Mengirim pesan ke WebSocket.
    2. Menjadwalkan ulang dirinya sendiri jika alarmnya berulang.
    """
    try:
        alarm = Alarm.objects.get(pk=alarm_id)
    except Alarm.DoesNotExist:
        print(f"ALARM TASK: Alarm dengan ID {alarm_id} tidak ditemukan. Berhenti.")
        return

    # --- Kirim Pesan ke WebSocket ---
    channel_layer = get_channel_layer()
    group_name = f'grup_{alarm.modul.serial_id}'

    # ubah pesan sesuai kebutuhan
    message_payload = {
        'type': 'alarm_triggered',
        'alarm_id': alarm.id,
        'label': alarm.label,
        'time': alarm.time.strftime('%H:%M:%S'),
        'message': f"ALARM AKTIF: {alarm.label or 'Alarm'} pada {alarm.time.strftime('%H:%M:%S')}"
    }
    print(f"ALARM TASK: Memicu alarm untuk grup '{group_name}'")
    
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'channel.message',
            'message': json.dumps(message_payload),
            'sender_channel_name': 'celery_worker'
        }
    )

    # --- Jadwalkan Ulang ---
    # Jika alarmnya masih aktif dan merupakan alarm berulang
    if alarm.is_active and alarm.is_repeating:
        from smartfarming.utils.schedule import schedule_alarm_task
        print(f"ALARM TASK: Menjadwalkan ulang untuk alarm berulang ID {alarm_id}...")
        schedule_alarm_task(alarm)
    else:
        # Jika tidak berulang, hapus ID tugas agar tidak ada sisa
        alarm.celery_task_id = None
        alarm.save()
        print(f"ALARM TASK: Alarm sekali jalan ID {alarm_id} selesai.")