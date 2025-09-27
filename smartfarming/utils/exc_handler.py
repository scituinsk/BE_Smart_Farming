from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        detail = response.data.get("detail") if "detail" in response.data else response.data
        response.data = {
            "success": False,
            "message": detail,
            "errors": response.data,
            "data": None,
        }
    return response


class CustomResponse(Response):
    def __init__(self, data=None, message="", success=True, errors=None, status=None, **kwargs):
        standard_format = {
            "success": success,
            "status": status,
            "message": message,
            "errors": errors if errors else False,
            "data": data,
        }
        super().__init__(standard_format, status=status, **kwargs)
