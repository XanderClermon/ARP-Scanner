import redis
from config import settings


class SignalManager:
    def __init__(self):
        self.r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self.last_id = '$'  # '$' означает, что мы читаем только НОВЫЕ сообщения с момента запуска

    def get_latest_command(self):
        """Проверяет стрим на наличие новых команд"""
        if not settings.USE_WEB_CONTROL:
            return None

        # XREAD читает новые записи. block=10 означает ждать 10мс, если пусто
        streams = self.r.xread({settings.STREAM_NAME: self.last_id}, count=1, block=10)

        if streams:
            for stream_name, messages in streams:
                for msg_id, data in messages:
                    self.last_id = msg_id
                    cmd = data.get('command')
                    print(f"[DEBUG] Менеджер увидел команду в Redis: {cmd}")  # <-- ДЕБАГ ЛОГ
                    return cmd

        return None