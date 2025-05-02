import Helpers.DisplayColors as Colors
import Helpers.DisplayNames as DisplayNames
import Helpers.DeviceNames as DeviceNames
import Helpers.DeviceStates as DeviceStates
import Helpers.Helpers as Helpers
import Helpers.LcdCustomSymbols as Symbols
from ..Driver.WSLCD1602RGB import  WSLCD1602RGB
from .Screen import Screen
from State.States import States

class HeaterPowerSwithScreen(Screen):

    def __init__(self, lcd:WSLCD1602RGB, states:States):
        self._states = states
        super().__init__(
            lcd = lcd, 
            screen_name = DisplayNames.HEATER_POWER_LOAD_SCREEN_NAME,
            device_name = DeviceNames.HEATER_POWER_SWITH_KEY, 
            screen_title = f"{Symbols.HEATING}|Heater Swith",
            color = Colors.BLUE_AND_WHITE
        )
    
    def present(self):
        current_value = self._states.get_heater_state(self.get_device_name())
        preview_value = self._states.get_heater_preview_state(self.get_device_name())
        if not str(current_value):
            current_value = self.get_default_text()
        self.show(f"State: {current_value}")
    


