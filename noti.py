from plyer import notification
from interfaces import BaseNotifier

class WindowsNotifier(BaseNotifier):
    def send(self, title: str, message: str):
        notification.notify(
            title="New Device Found",
            message="New Device Found",
            app_name="NetDemon",
            timeout=5,
            ticker="Notification",
        )
