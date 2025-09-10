import Helpers.DisplayColors as Colors
import Helpers.DisplayNames as DisplayNames
import Helpers.DeviceNames as DeviceNames
import Resources.Settings as Settings
from ..Driver.WSLCD1602RGB import  WSLCD1602RGB
from .Screen import Screen
from RTC.DsRTC import DsRTC

class StartingScreen(Screen):
    def __init__(self, lcd: WSLCD1602RGB):
        self._status = "Initializing..."
        version_title = f"Starting... v{Settings.APP_VERSION}"
        
        super().__init__(
            lcd = lcd, 
            screen_name = DisplayNames.LOADING_SCREEN_NAME,
            device_name = DeviceNames.LCD_DEVICE_KEY, 
            screen_title = version_title,
            color = Colors.BLUE_AND_WHITE
        )

    def present(self):
        self.show(self._status)
    
    def update_status(self, status: str):
        """Update initialization status"""
        self._status = status[:16] if len(status) > 16 else status
        self.update_description(self._status)