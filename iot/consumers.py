import json
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
        Menerima pesan, membedakan antara 'perintah' dan 'status',
        lalu menyiarkannya ke anggota grup LAIN.
        """
        sender_channel_name = self.channel_name
        message_to_broadcast = ""
        
        try:
            data_dict = json.loads(text_data)

            if 'command' in data_dict:
                command = data_dict.get('command', '').upper()
                duration = data_dict.get('duration', 0)
                # Terjemahkan ke format sederhana untuk ESP32
                message_to_broadcast = f"{command}:{duration}"
                print(f"WS> Translating command to simple text: '{message_to_broadcast}'")
     
            else:
                message_to_broadcast = text_data
                print(f"WS> Forwarding status message: '{message_to_broadcast}'")

        except json.JSONDecodeError:
            print(f"WS> Ignoring non-JSON message: {text_data}")
            return

        # Hanya siarkan jika ada pesan yang valid untuk disiarkan
        if message_to_broadcast:
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'broadcast.message',
                    'message': message_to_broadcast,
                    'sender_channel_name': sender_channel_name
                }
            )

    async def broadcast_message(self, event):
        """Menerima pesan dari grup dan meneruskannya ke client."""
        message = event['message']
        sender_channel_name = event['sender_channel_name']

        if self.channel_name != sender_channel_name:
            await self.send(text_data=message)
            print(f"WS> Broadcasting to {self.channel_name}: {message}")