from channels.generic.websocket import AsyncWebsocketConsumer

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