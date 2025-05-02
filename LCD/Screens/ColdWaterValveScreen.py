import Helpers.DisplayColors as Colors
import Helpers.DisplayNames as DisplayNames
import Helpers.DeviceNames as DeviceNames
import Helpers.DeviceStates as DeviceStates
import Helpers.LcdCustomSymbols as Symbols
from ..Driver.WSLCD1602RGB import  WSLCD1602RGB
from .Screen import Screen
from State.States import States

class ColdWaterValveScreen(Screen):
    
    _error_color = Colors.RED

    def __init__(self, lcd: WSLCD1602RGB, states:States):
        self.states = states
        super().__init__(
            lcd = lcd, 
            screen_name = DisplayNames.COLD_WATER_VALVE_SCREEN_NAME, 
            device_name = DeviceNames.COLD_WATER_VALVE_KEY, 
            screen_title = f"{Symbols.VALVE}|Cold valve",
            color = Colors.BLUE_AND_WHITE
        )

    def present(self):
        state = self.states.get_valve_state(self.get_device_name())
        self.show(self._get_text_by_state(state), self._get_color_by_state(state))

    def _get_text_by_state(self, state) -> str :
        states = {
            DeviceStates.CLOSED: f"State: {Symbols.LOCK} Close",
            DeviceStates.OPENED: f"State: {Symbols.UNLOCK} Open",
            DeviceStates.CLOSING: "State: Closing...",
            DeviceStates.OPENING: "State: Opening...",
            DeviceStates.ERROR: "State: Error"
        }

        return states.get(state, "State: --")
        
    def _get_color_by_state(self, state):
        return self._error_color if state == DeviceStates.ERROR else self.get_default_color() 
