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
        try:
            data_dict = json.loads(text_data)
            print(f"WS> Received from client: {data_dict}")

            command = data_dict.get('command', 'OFF').upper()
            duration = data_dict.get('duration', 0)
            payload_for_mqtt = f"{command}:{duration}"
            topic = f"devices/{self.device_id}/control"
            publish_message(topic, payload_for_mqtt)

            print(f"WS> Forwarded to MQTT topic '{topic}': {payload_for_mqtt}")

        except Exception as e:
            print(f"WS> An error occurred: {e}")

    # Menerima pesan dari channel layer (dari subscriber MQTT)
    async def device_message(self, event):
        message = event['message']

        # Kirim pesan ke WebSocket (ke Frontend)
        await self.send(text_data=json.dumps(message))