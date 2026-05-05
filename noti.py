from plyer import notification
from interfaces import BaseNotifier

class WindowsNotifier(BaseNotifier):
    def send(self, title: str, message: str):
        notification.notify(
            title,
            message,
            app_name="NetDemon",
            timeout=5,
            ticker="Notification",
        )

class SilentNotifier(BaseNotifier):
    def send(self, title: str, message: str):
        pass