import json
from channels.generic.websocket import AsyncWebsocketConsumer
from utils.mqtt import publish_message

class DeviceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Mengambil device_id dari URL
        self.device_id = self.scope['url_route']['kwargs']['device_id']
        self.group_name = f'device_{self.device_id}'

        # Bergabung ke grup broadcast
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Meninggalkan grup
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Menerima pesan dari WebSocket (dari Frontend)
    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data['command']

        # Publish pesan ke MQTT untuk dikirim ke ESP32
        topic = f"devices/{self.device_id}/control"
        payload = json.dumps({"command": command})
        publish_message(topic, payload)

    # Menerima pesan dari channel layer (dari subscriber MQTT)
    async def device_message(self, event):
        message = event['message']

        # Kirim pesan ke WebSocket (ke Frontend)
        await self.send(text_data=json.dumps(message))