import json
from django.core.management.base import BaseCommand
from django.conf import settings
import paho.mqtt.client as mqtt
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class Command(BaseCommand):
    help = 'Starts the MQTT client to subscribe to topics'

    def handle(self, *args, **kwargs):
        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message

        self.stdout.write(self.style.SUCCESS("Connecting to MQTT broker..."))
        client.connect(
            settings.MQTT_BROKER_HOST,
            settings.MQTT_BROKER_PORT,
            settings.MQTT_KEEPALIVE
        )

        # loop_forever() adalah blocking call, ia akan berjalan terus
        # sampai program dihentikan.
        client.loop_forever()

    def on_connect(self, client, userdata, flags, rc):
        """Callback yang dipanggil saat berhasil terhubung ke broker."""
        if rc == 0:
            self.stdout.write(self.style.SUCCESS("Successfully connected to MQTT broker."))
            client.subscribe("devices/+/status")
            self.stdout.write(self.style.SUCCESS("Subscribed to topic: devices/+/status"))
        else:
            self.stdout.write(self.style.ERROR(f"Failed to connect, return code {rc}\n"))

    def on_message(self, client, userdata, msg):
        self.stdout.write(f"MQTT> Received message on topic {msg.topic}: {msg.payload.decode()}")

        try:
            data = json.loads(msg.payload.decode())
            device_id = msg.topic.split('/')[1]
            group_name = f'device_{device_id}'

            # Dapatkan channel layer
            channel_layer = get_channel_layer()

            # Kirim data ke grup WebSocket yang sesuai
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'device.message', # Ini akan memanggil method device_message di consumer
                    'message': data
                }
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))