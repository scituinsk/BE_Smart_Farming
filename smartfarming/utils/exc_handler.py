from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.utils import timezone

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        request = context.get("request")
        detail = response.data.get("detail", response.data)
        response.data = {
            "success": False,
            "status": response.status_code,
            "message": detail,
            "path": request.path if request else None,
            "timestamp": timezone.now().isoformat().replace("+00:00", "Z"),
            "data": None,
        }

    return response



class CustomResponse(Response):
    def __init__(self, data=None, message="Ok", success=True, status=None, request=None,**kwargs):
        standard_format = {
            "success": success,
            "status": status,
            "message": message,
            "path": request.path if request else None,
            "timestamp": timezone.now().isoformat().replace("+00:00", "Z"),
            "data": data,
        }
        super().__init__(standard_format, status=status, **kwargs)
