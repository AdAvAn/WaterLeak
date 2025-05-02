import Helpers.DisplayColors as Colors
import Helpers.DisplayNames as DisplayNames
import Helpers.DeviceNames as DeviceNames
import Helpers.DeviceStates as DeviceStates
import Helpers.LcdCustomSymbols as Symbols
from ..Driver.WSLCD1602RGB import WSLCD1602RGB
from .Screen import Screen
from State.States import States


class LeakZone1Screen(Screen):
    
    _error_color = Colors.RED

    def __init__(self, lcd: WSLCD1602RGB, states:States):
        self.states = states
        super().__init__(
            lcd = lcd, 
            screen_name = DisplayNames.LEAK_ZONE1_SCREEN_NAME,
            device_name = DeviceNames.ZONE_1_LEAK_SENSORS_KEY, 
            screen_title = f"{Symbols.DROPLET}|Leak zone 1",
            color = Colors.BLUE_AND_WHITE
        )

    def present(self):
        state = self.states.get_leak_sensor_state(self.get_device_name())
        self.show(self.get_text(state), self.get_color(state))

    def get_text(self, state) -> str:
        text =  f"Leak {Symbols.CROSS}" if state == DeviceStates.LEAK else f"No leak {Symbols.CHECK}"
        return "State: " + text
        
    def get_color(self, state):
        return self._error_color if state == DeviceStates.LEAK else self.get_default_color()