import Helpers.DisplayColors as Colors
import Helpers.DisplayNames as DisplayNames
import Helpers.DeviceNames as DeviceNames
from ..Driver.WSLCD1602RGB import WSLCD1602RGB
from .Screen import Screen

class ErrorScreen(Screen):
    
    def __init__(self, lcd: WSLCD1602RGB, error_code: str, error_text = None):
        self.error_code = error_code
        self.error_text = error_text
        super().__init__(
            lcd = lcd, 
            screen_name = "ErrorScreen",
            device_name = DeviceNames.LCD_DEVICE_KEY, 
            screen_title = f"Error: {error_code}",
            color = Colors.RED
        )

    def present(self):
        message = self.error_text if self.error_text else "System Error"
        self.show(message)