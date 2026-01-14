import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from iot.models import *
from schedule.models import GroupSchedule
from smartfarming.tasks import task_broadcast_module_notification
from profil.models import NotificationType, Notification
import asyncio
import logging

logger = logging.getLogger(__name__)

class DeviceAuthConsumer(AsyncWebsocketConsumer):
    """ KETENTUAN PENGIRIMAN PESAN KE AUTH WEBSOCKET
    - url koneksi adalah ws://domain.com/ws/device/<serial_id>/
    - grup websocket merupakan grup_<serial_id>
    - <serial_id> dan <auth_id> didapatkan dari database modul
    - perangkat iot harus mengirimkan pesan setidaknya sekali untuk mendapatkan pesan dari user
    - jika pesan dikirim dari user maka harus menambahkan Autorization dengan value Bearer {{access_token}}
    - jika pesan dikirim dari perangkat IoT maka harus dalam format json dan wajib ada {"device": "{{auth_id}}"}
    - jika mengirim pesan tanpa header Autorization atau json {"device": "{{auth_id}}"} maka akan dianggap sebagai anonim
    - jika ada anonim connect ke wss maka pesan tidak akan dikirimkan ke grup websocket manapun
    """
    async def connect(self):
        """
        Dipanggil saat koneksi WebSocket baru dibuat.
        Memvalidasi serial_id dan user yang login.
        """
        #ambil serial_id dari URL
        self.serial_id = self.scope['url_route']['kwargs']['serial_id']
        self.group_name = f'grup_{self.serial_id}'
        self.user = self.scope['user']
        self.connection_accepted = False

        # apakah modul dengan serial_id ini ada di database
        self.modul = await self.get_modul()
        if self.modul is None:
            logger.warning(f"WS> REJECTED: Modul dengan serial_id {self.serial_id} tidak ditemukan.")
            await self.close()
            return

        if self.user.is_authenticated:
            is_member = await self.is_user_member_of_modul()
            if not is_member:
                logger.warning(f"WS> REJECTED: User {self.user.username} tidak punya akses ke modul {self.serial_id}.")
                await self.close()
                return
            
            # user sah, langsung tambahkan ke grup
            await self.add_to_group()
            logger.info(f"WS> User {self.user.username} ({self.channel_name}) terhubung ke grup '{self.group_name}'")
        else:
            # Jika koneksi tanpa user (kemungkinan dari perangkat IoT),
            # kita terima koneksi tapi belum dimasukkan ke grup.
            # Perangkat harus mengirim pesan otentikasi terlebih dahulu.
            logger.info(f"WS> Perangkat ({self.channel_name}) terhubung, menunggu otentikasi untuk grup '{self.group_name}'")

        # Terima koneksi
        await self.accept()
        await self.send(text_data=json.dumps({"status": "Connected to Websocket"}))

    async def disconnect(self, close_code):
        """Dipanggil saat koneksi ditutup."""
        await self.send(text_data=json.dumps({"status": "Disconnected from Websocket"}))
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.warning(f"WS> Client {self.channel_name} terputus dari grup '{self.group_name}'")

    async def receive(self, text_data):
        """
        Optimized receive method:
        1. Parallel processing untuk penyimpanan DB sensor.
        2. Structured error handling untuk tracing.
        3. Efficient broadcasting.
        """
        try:
            # TRACING INPUT & PARSING
            # Cek tipe data agar fleksibel (String/Bytes/Dict)
            if isinstance(text_data, (dict, list)):
                data = text_data
                # Jika input sudah dict, kita butuh string-nya untuk broadcast hemat resource
                payload_string = json.dumps(data) 
            else:
                # Jika text_data adalah string/bytes
                data = json.loads(text_data)
                payload_string = text_data

            # VALIDASI tipe data
            if not isinstance(data, dict):
                logger.warning(f"WS-PARSE> Payload bukan dictionary: {data} ({type(data)})")
                await self._handle_user_message(payload_string)
                return

            # LOGIC PEMROSESAN
            
            # KASUS A: Pesan dari PERANGKAT (Ada key 'device')
            device_auth = data.get("device", None)

            if device_auth is not None:
                device_auth_id = data.get('device')

                # Validasi Auth
                if str(self.modul.auth_id) != device_auth_id:
                    logger.warning(f"WS-SECURITY> Device Auth Gagal. ID: {self.serial_id}, Input: {device_auth_id}")
                    return
                device_log_payload = data.get("device_logs")
                if device_log_payload:
                    await self.create_module_log(device_log_payload)

                # Mapping: Kunci JSON -> Fungsi Handler
                # Tips: Jika nambah sensor baru, cukup tambah di sini.
                sensor_handlers = {
                    'temperature_data': self.update_temperature_data,
                    'humidity_data': self.update_humidity_data,
                    'battery_data': self.update_battery_data,
                    'water_level_data': self.update_water_level_data,
                }

                # Kumpulkan tugas (tasks) yang valid
                tasks = []
                for key, handler in sensor_handlers.items():
                    if key in data:
                        # panggil fungsi tapi jangan di-await dulu
                        tasks.append(handler(data[key]))

                # EFISIENSI: Jalankan semua update database secara PARALEL
                if tasks:
                    # return_exceptions=True agar jika 1 sensor error, yang lain tetap tersimpan
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Tracing error parsial (misal suhu sukses, tapi baterai gagal)
                    for i, res in enumerate(results):
                        if isinstance(res, Exception):
                            logger.error(f"WS-TASK> Error pada task sensor: {res}")

                # Logic Grup & Broadcast
                await self.add_to_group()
                await self.broadcast_message_to_group(payload_string) # Kirim string asli (hemat CPU)
                
                logger.info(f"WS-OK> Device {self.serial_id}: Data processed & broadcasted.")

            # KASUS B: Pesan dari USER (Tidak ada key 'device')
            else:
                await self._handle_user_message(payload_string)

        except json.JSONDecodeError as e:
            # Error Parsing JSON spesifik
            logger.error(f"WS-PARSE> JSON Error di baris {e.lineno}: {e.msg}. Data: {text_data}...")
            # Fallback: Mungkin user kirim raw text, coba handle sebagai pesan user
            await self._handle_user_message(text_data)

        except Exception as e:
            # Error tak terduga lainnya
            logger.exception(f"WS-CRITICAL> Error tak terduga di receive: {str(e)}")

    async def _handle_user_message(self, message):
        """Helper untuk memproses pesan user agar kode utama rapi"""
        if self.user.is_authenticated and await self.is_user_member_of_modul():
            await self.broadcast_message_to_group(message)
            logger.info(f"WS-USER> User {self.user.username} broadcast pesan.")
        else:
            logger.warning(f"WS-SECURITY> Akses user ditolak di grup {self.group_name}.")

    async def broadcast_message_to_group(self, message):
        """Helper untuk mengirim pesan ke channel layer."""
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'channel.message',
                'message': message,
                'sender_channel_name': self.channel_name
            }
        )

    async def channel_message(self, event):
        """Menerima pesan dari grup dan mengirimkannya ke client."""
        message = event['message']
        sender_channel_name = event['sender_channel_name']

        # Jika pengirimnya adalah celery_worker, kirim ke semua.
        # Jika pengirimnya adalah client lain, jangan kirim kembali ke pengirim.
        if sender_channel_name == 'celery_worker' or self.channel_name != sender_channel_name:
            await self.send(text_data=message)

    async def add_to_group(self):
        """Helper untuk menambahkan channel ke grup."""
        await self.channel_layer.group_add(self.group_name, self.channel_name)

    # --- Fungsi Bantuan untuk Akses Database ---
    @database_sync_to_async
    def get_modul(self):
        """Mengambil instance Modul dari database secara async."""
        try:
            return Modul.objects.get(serial_id=self.serial_id)
        except Modul.DoesNotExist:
            return None

    @database_sync_to_async
    def is_user_member_of_modul(self):
        """Mengecek apakah user adalah member dari modul ini."""
        # Query many-to-many: cek apakah user ada di dalam `self.modul.user.all()`
        return self.modul.user.filter(pk=self.user.pk).exists()
    
    @database_sync_to_async
    def create_module_log(self, payload: dict):
        try:
            # Ekstraksi Value dari payload
            log_id = payload.get("id")
            log_type = payload.get("type", "modul")
            name = payload.get("name")
            log_data = payload.get("data", {})

            # jika ada id maka dia update log yang sudah ada
            if type(log_id) == type(123):
                pins = log_data.get("pins", [])
                modul_pin = ModulePin.objects.filter(module=self.modul)
                
                # Mapping: {6: "relay 1", 7: "relay 2"}
                pin_map = {mp.pin: mp.name for mp in modul_pin}
                
                # Update nilai pin di dalam list pins
                # Karena 'pins' adalah referensi ke dalam 'log_data', 
                # mengubah 'p' berarti mengubah isi 'log_data' juga.
                for p in pins:
                    original_pin = p.get("pin")
                    # Ganti angka dengan nama jika ada di map, jika tidak biarkan angkanya
                    if original_pin in pin_map:
                        p["pin"] = pin_map[original_pin]

                update_log = ModuleLog.objects.get(id=log_id)
                schedule_name = GroupSchedule.objects.get(id= update_log.schedule.id)
                
                # Simpan 'log_data' yang strukturnya sudah benar & terupdate
                update_log.data = log_data 
                update_log.save()
                task_broadcast_module_notification.delay(modul_id=self.modul.id, title=f"Penjadwalan {schedule_name.name} dipicu!", body="IoT sedang menjalankan tugas", data=log_data)
                users = self.modul.user.all()
                Notification.bulk_create_for_users(users=users, notif_type=NotificationType.SCHEDULE, title=f"Penjadwalan {schedule_name.name} dipicu!", body="IoT sedang menjalankan tugas", data=log_data)
                logger.info(
                    f"DB> Log diperbarui | module={self.modul.serial_id} | type={update_log.type}"
                )
            else:                
                if name == None:
                    name = self.modul.name
                ModuleLog.objects.create(
                    module=self.modul,
                    type=log_type,
                    name=name,
                    data=log_data # Simpan data dict mentah
                )

                logger.info(
                    f"DB> Log dibuat | module={self.modul.serial_id} | type={log_type}"
                )

        except Exception as e:
            logger.exception(f"Gagal membuat ModuleLog: {e}")

    @database_sync_to_async
    def update_temperature_data(self, message):
        """
        Fungsi untuk membuat objek ScheduleLog di database secara asynchronous.
        """
        try:
            feature = Feature.objects.get(name='temperature')
            data_modul, created = DataModul.objects.update_or_create(modul=self.modul, feature=feature, defaults={'data': message})

            # Periksa boolean 'created'
            if created:
                logger.info(f"DB> Data temperatur BERHASIL DIBUAT untuk modul {self.modul.serial_id}.")
            else:
                logger.info(f"DB> Data temperatur BERHASIL DIUPDATE untuk modul {self.modul.serial_id}.")
        except Exception as e:
            logger.exception(f"DB> GAGAL menambahkan data: {e}")

    @database_sync_to_async
    def update_humidity_data(self, message):
        """
        Fungsi untuk membuat objek ScheduleLog di database secara asynchronous.
        """
        try:
            feature = Feature.objects.get(name='humidity')
            data_modul, created = DataModul.objects.update_or_create(modul=self.modul, feature=feature, defaults={'data': message})

            # Periksa boolean 'created'
            if created:
                logger.info(f"DB> Data humidity BERHASIL DIBUAT untuk modul {self.modul.serial_id}.")
            else:
                logger.info(f"DB> Data humidity BERHASIL DIUPDATE untuk modul {self.modul.serial_id}.")
        except Exception as e:
            logger.exception(f"DB> GAGAL menambahkan data: {e}")

    @database_sync_to_async
    def update_battery_data(self, message):
        """
        Fungsi untuk membuat objek ScheduleLog di database secara asynchronous.
        """
        try:
            feature = Feature.objects.get(name='battery')
            data_modul, created = DataModul.objects.update_or_create(modul=self.modul, feature=feature, defaults={'data': message})

            # Periksa boolean 'created'
            if created:
                logger.info(f"DB> Data battery BERHASIL DIBUAT untuk modul {self.modul.serial_id}.")
            else:
                logger.info(f"DB> Data battery BERHASIL DIUPDATE untuk modul {self.modul.serial_id}.")
        except Exception as e:
            logger.exception(f"DB> GAGAL menambahkan data: {e}")
    
    @database_sync_to_async
    def update_water_level_data(self, message):
        """
        Fungsi untuk membuat objek ScheduleLog di database secara asynchronous.
        """
        try:
            feature = Feature.objects.get(name='water_level')
            data_modul, created = DataModul.objects.update_or_create(modul=self.modul, feature=feature, defaults={'data': message})

            # Periksa boolean 'created'
            if created:
                logger.info(f"DB> Data water level BERHASIL DIBUAT untuk modul {self.modul.serial_id}.")
            else:
                logger.info(f"DB> Data water level BERHASIL DIUPDATE untuk modul {self.modul.serial_id}.")
        except Exception as e:
            logger.exception(f"DB> GAGAL menambahkan data: {e}")