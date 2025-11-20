import json
from channels.generic.websocket import AsyncWebsocketConsumer

class LogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        
        # HANYA Staff/Admin yang boleh masuk
        if user.is_authenticated and user.is_staff:
            await self.channel_layer.group_add("admin_logs_group", self.channel_name)
            await self.accept()
            await self.send(text_data=json.dumps({"status": "Connected to Log Stream"}))
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("admin_logs_group", self.channel_name)

    # Handler untuk pesan tipe 'log.message' dari Handler
    async def log_message(self, event):
        log_data = event['data']
        await self.send(text_data=json.dumps(log_data))