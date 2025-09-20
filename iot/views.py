import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.mqtt import publish_message

class ControlDeviceView(APIView):
    """
    Endpoint untuk mengirim perintah ke perangkat melalui MQTT.
    """
    def post(self, request, *args, **kwargs):
        device_id = request.data.get('device_id')
        command = request.data.get('command')
        print(request.data)

        if not device_id or not command:
            return Response(
                {"error": "device_id and command are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        topic = f"devices/{device_id}/control"
        payload = json.dumps({"command": command, "source": "api"})

        # Kirim pesan
        success = publish_message(topic, payload)
        # success = True

        if success:
            return Response(
                {"message": f"Command '{command}' sent to device '{device_id}'."},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "Failed to send command via MQTT."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )