from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import AnonymousUser, User
from channels.db import database_sync_to_async
from urllib.parse import parse_qs

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()

class JwtAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Cari token dari query string (untuk client browser)
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        # Jika tidak ada di query string, cari di header (untuk Postman/client non-browser)
        if not token:
            headers = dict(scope['headers'])
            auth_header = headers.get(b'authorization', b'').decode('utf-8')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if token:
            try:
                # Validasi token
                access_token = AccessToken(token)
                # Ambil user dari database
                scope['user'] = await get_user(user_id=access_token['user_id'])
            except Exception as e:
                # Token tidak valid atau kedaluwarsa
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)