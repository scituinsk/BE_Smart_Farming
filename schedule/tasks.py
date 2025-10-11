from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

@shared_task(name="trigger_alarm_task")
def trigger_alarm_task(serial_id, alarm_id, alarm_label, alarm_time_str):
    """
    Tugas Celery yang dijalankan saat alarm berbunyi.
    Tugas ini mengirimkan pesan ke grup WebSocket yang sesuai.
    """
    channel_layer = get_channel_layer()
    group_name = f'grup_{serial_id}'
    
    # Pesan yang akan dikirim ke perangkat/dashboard
    message_payload = {
        'type': 'alarm_triggered',
        'alarm_id': alarm_id,
        'label': alarm_label,
        'time': alarm_time_str,
        'message': f"ALARM AKTIF: {alarm_label or 'Alarm'} pada {alarm_time_str}"
    }

    print(f"CELERY WORKER: Memicu alarm untuk grup '{group_name}'")
    
    # Mengirim pesan ke channel layer (WebSocket group)
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'channel.message',
            'message': json.dumps(message_payload),
            'sender_channel_name': 'celery_worker'
        }
    )