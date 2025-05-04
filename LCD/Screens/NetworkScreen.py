import Helpers.DisplayColors as Colors
import Resources.Settings as Settings
import Helpers.DeviceNames as DeviceNames
from ..Driver.WSLCD1602RGB import WSLCD1602RGB
from .Screen import Screen
from Helpers.WiFiManager import WiFiManager

class NetworkScreen(Screen):
    def __init__(self, lcd: WSLCD1602RGB):
        self.wifi_manager = WiFiManager()
        super().__init__(
            lcd = lcd, 
            screen_name = "NetworkScreen",
            device_name = DeviceNames.LCD_DEVICE_KEY, 
            screen_title = f"WiFi: ({Settings.WIFI_SSID})",
            color = Colors.BLUE_AND_WHITE
        )
    
    def present(self):
        ip_address = self.wifi_manager.get_ip_address()
        message = "Not Connected" if ip_address is None else f"{ip_address}"
        self.show(message)