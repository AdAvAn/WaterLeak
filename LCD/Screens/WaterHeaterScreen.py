import Helpers.DisplayColors as Colors
import Helpers.DisplayNames as DisplayNames
import Helpers.DeviceNames as DeviceNames
import Helpers.Helpers as Helpers
import Helpers.LcdCustomSymbols as Symbols
from ..Driver.WSLCD1602RGB import WSLCD1602RGB
from .Screen import Screen
from State.States import States

class WaterHeaterScreen(Screen):

    def __init__(self, lcd: WSLCD1602RGB, states:States):
        self.states = states
        super().__init__(
            lcd = lcd, 
            screen_name = DisplayNames.WATER_HEATER_SCREEN_NAME,
            device_name = DeviceNames.HEATER_TEMP_SENSORS_KEY, 
            screen_title = f"{Symbols.TEMPERATURE}|Heater",
            color = Colors.BLUE_AND_WHITE
        )
    
    def present(self):
        current_temp = self.states.get_temperature(self.get_device_name())
        preview_temp = self.states.get_temperature_preview_state(self.get_device_name())
        
        # Handle sensor errors and missing sensors
        if current_temp == "No temp sensor":
            self.show("Sensor not found", Colors.ORANGE)
            return
        elif current_temp == "ERROR":
            self.show("Sensor error", Colors.RED)
            return
        elif not current_temp:
            current_temp = self.get_default_text()
            
        trend = self.get_trand(current_temp, preview_temp)
        self.show(f"Temp: {current_temp} {Symbols.DEGREES}C {trend}")

    def get_trand(self, current_temp, preview_temp) -> str:
        # Handle error states
        if current_temp in ["No temp sensor", "ERROR", self.get_default_text()]:
            return ""
        if preview_temp in ["No temp sensor", "ERROR", None]:
            return ""
            
        trend = Helpers.get_trand(current_temp, preview_temp) 
        variants = {"up":Symbols.UP, "down":Symbols.DWON}
        return variants.get(trend, "")