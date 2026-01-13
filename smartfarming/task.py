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
def task_broadcast_module_notification(modul_id, title, body, data=None, exclude_user_id=None):
    """
    Task untuk broadcast notifikasi ke SEMUA user yang terhubung dengan Modul tertentu
    task_broadcast_module_notification.delay()
    
    :param modul_id: ID (Primary Key) dari Modul
    :param exclude_user_id: (Opsional) ID user yang TIDAK perlu dikirim notifikasi (misal: user yang melakukan aksi itu sendiri).
    """
    try:
        modul = Modul.objects.get(id=modul_id)
        users = modul.user.all()
        devices = FCMDevice.objects.filter(user__in=users, active=True)
        if exclude_user_id:
            devices = devices.exclude(user_id=exclude_user_id)

        if data is None: 
            data = {}
        if isinstance(data, str):
            logger.warning(f"Data dikirim sebagai string, bukan dict: {data}")
            # jSika string json valid, bisa diparse. Jika tidak, jadikan value
            data = {"message_payload": data} 

        clean_data = {k: str(v) for k, v in data.items()}
        clean_data['module_serial_id'] = str(modul.serial_id)

        # fcm-django akan otomatis menangani batching jika device > 500
        if devices.exists():
            devices.send_message(
                message=Message(
                    notification=Notification(title=title, body=body),
                    data=clean_data
                )
            )
            logger.info(f"Berhasil broadcast ke {devices.count()} device(s) untuk modul {modul_id}")
        else:
            devices.send_message(
                message=Message(
                    notification=Notification(title=f"Device {modul.name} tidak aktif untuk menerima tugas!", body=body)
                )
            )
            logger.info(f"Device {modul.name} tidak aktif")
            
            
    except Modul.DoesNotExist:
        logger.warning(f"Modul dengan id {modul_id} tidak ditemukan.")
    except Exception as e:
        import traceback
        logger.error(f"Error broadcast notification: {e}")
        logger.error(traceback.format_exc())