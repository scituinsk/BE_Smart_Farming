import paho.mqtt.client as mqtt
from django.conf import settings

def publish_message(topic, payload):
    """Fungsi untuk mem-publish pesan ke topic MQTT."""
    try:
        client = mqtt.Client()
        client.connect(
            settings.MQTT_BROKER_HOST,
            settings.MQTT_BROKER_PORT,
            settings.MQTT_KEEPALIVE
        )
        client.publish(topic, payload)
        client.disconnect()
        print(f"Published to {topic}: {payload}")
        return True
    except Exception as e:
        print(f"Failed to publish to MQTT: {e}")
        return False