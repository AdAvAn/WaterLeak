import Helpers.DisplayColors as Colors
import Helpers.DisplayNames as DisplayNames
from ..Driver.WSLCD1602RGB import  WSLCD1602RGB
from .Screen import Screen

class AlarmScreen(Screen):

    def __init__(self, lcd: WSLCD1602RGB):
        self.text = None
        super().__init__(
            lcd = lcd, 
            screen_name = DisplayNames.ALARM_SCREEN,
            device_name = "", 
            screen_title = "Alarm",
            color = Colors.RED
        )

    def present(self):
        self.text = self.text if self.text is not None else ""
        self.show(self.text)

    def update_alarm(self, title:str, text):
        self.set_screen_title(title)
        self.text = text
       