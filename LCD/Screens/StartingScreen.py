import Helpers.DisplayColors as Colors
import Helpers.DisplayNames as DisplayNames
import Helpers.DeviceNames as DeviceNames
from ..Driver.WSLCD1602RGB import  WSLCD1602RGB
from .Screen import Screen
from RTC.DsRTC import DsRTC

class StartingScreen(Screen):
    def __init__(self, lcd: WSLCD1602RGB):
        super().__init__(
            lcd = lcd, 
            
            screen_name = DisplayNames.LOADING_SCREEN_NAME,
            device_name = DeviceNames.LCD_DEVICE_KEY, 
            screen_title = "Starting...",
            color = Colors.BLUE_AND_WHITE
        )

    def present(self):
        self.show(f"")
