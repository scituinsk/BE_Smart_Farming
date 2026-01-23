from celery import shared_task
from firebase_admin.messaging import Message, Notification
from fcm_django.models import FCMDevice
from iot.models import Modul 
import logging

logger = logging.getLogger(__name__)

@shared_task
def task_send_push_notification(user_id, title, body, data=None):
    """
    Task untuk mengirim notifikasi via FCM.
    - task_send_push_notification.delay()

    :param user_id: ID user penerima
    :param title: Judul notifikasi
    :param body: Isi pesan
    :param data: Dictionary optional (key:value). Value akan di-convert ke string.
    """
    if data is None:
        data = {}
    clean_data = {k: str(v) for k, v in data.items()}

    devices = FCMDevice.objects.filter(user_id=user_id, active=True)

    if devices.exists():
        devices.send_message(
            message=Message(
                notification=Notification(title=title, body=body),
                data=clean_data
            )
        )

@shared_task
def task_broadcast_module_notification(user_ids,modul_id, title, body, data=None, exclude_user_id=None):
    """
    Task untuk broadcast notifikasi ke SEMUA user yang terhubung dengan Modul tertentu
    task_broadcast_module_notification.delay()
    
    :param modul_id: ID (Primary Key) dari Modul
    :param exclude_user_id: (Opsional) ID user yang TIDAK perlu dikirim notifikasi (misal: user yang melakukan aksi itu sendiri).
    """
    try:
        devices = FCMDevice.objects.filter(user__in=user_ids, active=True)
        if exclude_user_id:
            devices = devices.exclude(user_id=exclude_user_id)

        if data is None:
            data = {}
        if isinstance(data, str):
            data = {"message_payload": data}

        clean_data = {k: str(v) for k, v in data.items()}

        if devices.exists():
            devices.send_message(
                message=Message(
                    notification=Notification(title=title, body=body),
                    data=clean_data
                )
            )

    except Exception as e:
         logger.error(f"Error broadcast notification: {e}", exc_info=True)