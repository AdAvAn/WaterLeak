import Helpers.DisplayColors as Colors
import Helpers.DisplayNames as DisplayNames
import Helpers.DeviceNames as DeviceNames
import Helpers.Helpers as Helpers
import Helpers.LcdCustomSymbols as Symbols
from ..Driver.WSLCD1602RGB import  WSLCD1602RGB
from .Screen import Screen
from State.States import States

class HotWaterScreen(Screen):

    def __init__(self, lcd: WSLCD1602RGB, states:States):
        self.states = states
        super().__init__(
            lcd = lcd, 
            screen_name = DisplayNames.HOT_WATER_SCREEN_NAME,
            device_name = DeviceNames.HOT_WATER_TEMP_SENSORS_KEY, 
            screen_title = f"{Symbols.TEMPERATURE}|Hot water",
            color = Colors.BLUE_AND_WHITE
        )
    
    def present(self):
        current_temp = self.states.get_temperature(self.get_device_name())
        preview_temp = self.states.get_temperature_preview_state(self.get_device_name())
        trend = self.get_trand(current_temp, preview_temp)
        if not current_temp:
            current_temp = self.get_default_text()
        self.show(f"Temp: {current_temp} {Symbols.DEGREES}C {trend}")

    def get_trand(self, current_temp, preview_temp) -> str:
        trend = Helpers.get_trand(current_temp, preview_temp) 
        variants = {"up":Symbols.UP, "down":Symbols.DWON}
        return variants.get(trend, "")
    
