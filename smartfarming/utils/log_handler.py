import logging
import asyncio
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class WebSocketLogHandler(logging.Handler):
    """
    Handler custom yang 'Thread-Safe' dan 'Async-Safe' 
    untuk mengirim log ke Django Channels.
    """
    def emit(self, record):
        try:
            # Payload
            msg = self.format(record)
            log_entry = {
                'timestamp': record.asctime if hasattr(record, 'asctime') else getattr(record, 'created', 0),
                'level': record.levelname,
                'module': record.module,
                'message': msg,
                'line': record.lineno
            }

            channel_layer = get_channel_layer()
            if not channel_layer:
                return

            # pengiriman async
            async def send_log_async():
                await channel_layer.group_send(
                    "admin_logs_group",
                    {
                        "type": "log_message",
                        "data": log_entry
                    }
                )

            # LOGIKA UTAMA
            try:
                # Cek apakah kita sedang berada di dalam event loop yang aktif (Daphne/Async View)
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    # Jika ada loop, jadwalkan task di background (Non-blocking)
                    loop.create_task(send_log_async())
                else:
                    # Loop ada tapi tidak running (jarang terjadi, tapi buat jaga-jaga)
                    raise RuntimeError("Loop not running")
            except RuntimeError:
                # Jika TIDAK ada event loop (Sync View / Management Command / Shell)
                # dipaksa pakai async_to_sync agar kode async bisa jalan di sync
                async_to_sync(send_log_async)()

        except Exception:
            self.handleError(record)