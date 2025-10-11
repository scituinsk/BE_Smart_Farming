import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from iot.models import Modul

class DeviceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.device_id = self.scope['url_route']['kwargs']['device_id']
        self.group_name = f'device_{self.device_id}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        print(f"WS> Client {self.channel_name} connected to group '{self.group_name}'")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"WS> Client {self.channel_name} disconnected from group '{self.group_name}'")

    async def receive(self, text_data):
        """
        Menerima pesan (baik perintah string dari web atau status JSON dari ESP32)
        dan menyiarkannya ke semua anggota LAIN dalam grup.
        Server tidak lagi menerjemahkan format, hanya meneruskan pesan apa adanya.
        """
        print(f"WS> Received from {self.channel_name}, forwarding message: {text_data}")

        # - Jika dari web, pesannya "PIN:CMD:DURASI_..."
        # - Jika dari ESP32, pesannya '{"status": {"2": "ON", ...}}'
        message_to_broadcast = text_data

        # Kirim pesan ke grup channel
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'broadcast.message',
                'message': message_to_broadcast,
                'sender_channel_name': self.channel_name
            }
        )

    async def broadcast_message(self, event):
        """
        Menerima pesan dari grup dan meneruskannya ke WebSocket client.
        Fungsi ini memastikan client tidak menerima pesannya sendiri kembali.
        """
        message = event['message']
        sender_channel_name = event['sender_channel_name']

        # Hanya kirim pesan jika penerima BUKAN pengirim aslinya
        if self.channel_name != sender_channel_name:
            await self.send(text_data=message)
            print(f"WS> Broadcasting to {self.channel_name}: {message}")


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
        print(self.user)

        # apakah modul dengan serial_id ini ada di database
        self.modul = await self.get_modul()
        if self.modul is None:
            print(f"WS> REJECTED: Modul dengan serial_id {self.serial_id} tidak ditemukan.")
            await self.close()
            return

        if self.user.is_authenticated:
            is_member = await self.is_user_member_of_modul()
            if not is_member:
                print(f"WS> REJECTED: User {self.user.username} tidak punya akses ke modul {self.serial_id}.")
                await self.close()
                return
            
            # user sah, langsung tambahkan ke grup
            await self.add_to_group()
            print(f"WS> User {self.user.username} ({self.channel_name}) terhubung ke grup '{self.group_name}'")
        else:
            # Jika koneksi tanpa user (kemungkinan dari perangkat IoT),
            # kita terima koneksi tapi belum dimasukkan ke grup.
            # Perangkat harus mengirim pesan otentikasi terlebih dahulu.
            print(f"WS> Perangkat ({self.channel_name}) terhubung, menunggu otentikasi untuk grup '{self.group_name}'")

        # Terima koneksi
        await self.accept()

    async def disconnect(self, close_code):
        """Dipanggil saat koneksi ditutup."""
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f"WS> Client {self.channel_name} terputus dari grup '{self.group_name}'")

    async def receive(self, text_data):
        """
        Menerima pesan dari WebSocket client (baik user atau perangkat).
        Memvalidasi pesan dan menyiarkannya ke grup.
        """
        try:
            data = json.loads(text_data)
            # Pesan dari PERANGKAT: berisi 'device' sebagai kunci otentikasi
            if 'device' in data:
                auth_id_from_device = data.get('device')
                
                # Validasi auth_id dari perangkat
                if str(self.modul.auth_id) == auth_id_from_device:
                    # Jika ini pertama kali perangkat mengirim pesan, tambahkan ke grup
                    await self.add_to_group()
                    
                    # Siarkan pesan status ke grup
                    await self.broadcast_message_to_group(json.dumps(data))
                    print(f"WS> Pesan dari perangkat sah {self.serial_id} disiarkan: {text_data}")
                else:
                    print(f"WS> GAGAL: Pesan dari perangkat {self.serial_id} dengan auth_id salah.")

            # Pesan dari USER: tidak berisi kunci 'device'
            else:
                # apakah user yang mengirim pesan ini sah
                if self.user.is_authenticated and await self.is_user_member_of_modul():
                    await self.broadcast_message_to_group(text_data)
                    print(f"WS> Pesan dari user sah {self.user.username} disiarkan: {text_data}")
                else:
                    print(f"WS> GAGAL: Pesan dari koneksi tidak sah di grup {self.group_name}.")

        except json.JSONDecodeError:
            # Jika pesan bukan JSON, anggap itu dari user (misalnya perintah string)
            if self.user.is_authenticated and await self.is_user_member_of_modul():
                await self.broadcast_message_to_group(text_data)
                print(f"WS> Pesan dari user sah {self.user.username} disiarkan: {text_data}")
            else:
                print(f"WS> GAGAL: Pesan dari koneksi tidak sah di grup {self.group_name}.")

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